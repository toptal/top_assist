import logging
import time
import typing
from dataclasses import dataclass

import backoff
import openai
from openai import OpenAI
from openai.types.beta import AssistantResponseFormatOptionParam
from openai.types.beta.threads import ImageFileContentBlock, ImageURLContentBlock, Message, RefusalContentBlock

from top_assist.configuration import open_ai_api_key
from top_assist.utils.service_cooldown import with_service_cooldown
from top_assist.utils.tracer import ServiceNames, tracer


@dataclass
class ThreadCompletion:  # noqa: D101
    message: str
    thread_id: str


class ContentlessMessageError(Exception):  # noqa: D101
    pass


class ImageFileContentBlockError(Exception):  # noqa: D101
    pass


class ImageURLContentBlockError(Exception):  # noqa: D101
    pass


class NoAssistantResponseError(Exception):  # noqa: D101
    pass


class RunFailedWithRateLimitError(Exception):  # noqa: D101
    pass


class RunExpiredError(Exception):  # noqa: D101
    pass


class RefusalContentBlockError(Exception):  # noqa: D101
    pass


@tracer.wrap(service=ServiceNames.open_ai.value)
def add_user_message_and_complete(
    user_message: str,
    *,
    assistant_id: str,
    thread_id: str | None = None,
    response_format: AssistantResponseFormatOptionParam = "auto",
) -> ThreadCompletion:
    client = OpenAI(api_key=open_ai_api_key)
    thread_id = __ensure_thread_exists(thread_id, client)
    __add_user_message(user_message, thread_id, client)
    return __run(client, assistant_id, thread_id, response_format)


def __ensure_thread_exists(thread_id: str | None, client: OpenAI) -> str:
    if thread_id is None:
        thread_id = client.beta.threads.create().id
        logging.info("New assistant thread created", extra={"thread_id": thread_id})
    else:
        logging.info("Assistant thread loaded", extra={"thread_id": thread_id})

    return thread_id


@with_service_cooldown(
    service_key="openai_assistant",
    is_rate_limit_error=lambda e: isinstance(e, openai.RateLimitError),
)
def __add_user_message(user_message: str, thread_id: str, client: OpenAI) -> None:
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message,
    )
    logging.info("Message added to assistant thread", extra={"thread_id": thread_id})


@with_service_cooldown(
    service_key="openai_assistant",
    is_rate_limit_error=lambda e: isinstance(e, RunFailedWithRateLimitError),
)
@backoff.on_exception(backoff.constant, RunExpiredError, max_tries=2)
def __run(
    client: OpenAI, assistant_id: str, thread_id: str, response_format: AssistantResponseFormatOptionParam
) -> ThreadCompletion:
    run = _Run.start(client, assistant_id, thread_id, response_format)
    return run.wait()


class _Run:
    @classmethod
    def start(
        cls,
        client: OpenAI,
        assistant_id: str,
        thread_id: str,
        response_format: AssistantResponseFormatOptionParam,
    ) -> typing.Self:
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            response_format=response_format,
        )
        instance = cls(client, assistant_id, thread_id, run.id)
        logging.debug("Assistant thread run started", extra=instance.log_extra)
        return instance

    def __init__(self, client: OpenAI, assistant_id: str, thread_id: str, run_id: str):
        self.client = client
        self.assistant_id = assistant_id
        self.thread_id = thread_id
        self.run_id = run_id
        self.log_extra = {
            "assistant_id": assistant_id,
            "thread_id": thread_id,
            "run_id": run_id,
        }

    def wait(self) -> ThreadCompletion:
        try:
            while True:
                completion = self.__check_completion()
                if completion is not None:
                    return completion

                logging.info("Waiting for run to complete...", extra=self.log_extra)
                time.sleep(2)
        except Exception:
            logging.exception("Error waiting for assistant thread run completion", extra=self.log_extra)
            raise

    def __check_completion(self) -> ThreadCompletion | None:
        run_status = self.client.beta.threads.runs.retrieve(
            thread_id=self.thread_id,
            run_id=self.run_id,
        )
        logging.debug("Assistant thread run status", extra={**self.log_extra, "status": run_status.status})

        if run_status.status in ("in_progress", "queued"):
            return None

        elif run_status.status == "completed":
            messages = self.client.beta.threads.messages.list(thread_id=self.thread_id).data
            extracted_response = self.__extract_response(messages)
            return ThreadCompletion(extracted_response, self.thread_id)

        elif run_status.status == "failed":
            if run_status.last_error:
                if run_status.last_error.code == "rate_limit_exceeded":
                    logging.warning(
                        "Run failed with rate limit error.",
                        extra={"error": run_status.last_error, **self.log_extra},
                    )
                    raise RunFailedWithRateLimitError
                error_message = f"Run failed with error: {run_status.last_error.message}."
            else:
                error_message = "Run failed without a specific error message."

            logging.error(error_message, extra=self.log_extra)
            return ThreadCompletion(error_message, self.thread_id)
        elif run_status.status == "expired":
            logging.error("Run expired", extra=self.log_extra)

            raise RunExpiredError

        else:
            raise NotImplementedError(f"Unexpected run status: {run_status.status}")

    def __extract_response(self, messages: list[Message]) -> str:
        lines = []
        # Messages are returned in reverse chronological order
        # so to build a full reply we should take most recent
        # assistant messages block and concatenate them in reverse order
        for message in messages:
            if message.role != "assistant":
                break
            if len(message.content) == 0:
                raise ContentlessMessageError

            for content in message.content:
                if isinstance(content, ImageFileContentBlock):
                    raise ImageFileContentBlockError

                if isinstance(content, ImageURLContentBlock):
                    raise ImageURLContentBlockError

                if isinstance(content, RefusalContentBlock):
                    raise RefusalContentBlockError

                lines.append(content.text.value)

        if not lines:
            raise NoAssistantResponseError

        lines.reverse()
        return "\n".join(lines)
