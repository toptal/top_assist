import logging
from collections.abc import Callable
from dataclasses import dataclass

from top_assist.configuration import base_assistant_id
from top_assist.open_ai.assistants.threads import add_user_message_and_complete


@dataclass
class ChatGPTAnswer:  # noqa: D101
    message: str
    assistant_thread_id: str


def query_chatgpt(
    question: str,
    assistant_thread_id: str | None = None,
    text_formatter: Callable[[str], str] = lambda text: text,
) -> ChatGPTAnswer:
    logging.debug("Querying ChatGPT directly", extra={"question": question})
    completion = add_user_message_and_complete(
        question,
        assistant_id=base_assistant_id,
        thread_id=assistant_thread_id,
    )
    completion.message = text_formatter(completion.message)
    return ChatGPTAnswer(message=completion.message, assistant_thread_id=completion.thread_id)
