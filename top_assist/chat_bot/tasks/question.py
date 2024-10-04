import json
import logging
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

import top_assist.database.interactions as db_interactions
from top_assist.auth.provider import UnauthenticatedUserError, authorize_for
from top_assist.configuration import slack_reply_questions_in_channels
from top_assist.confluence.policy import PageAccessPolicy
from top_assist.models.qa_interaction import QAInteractionDTO
from top_assist.semantic_router.router import route as route_with_semantic_router
from top_assist.semantic_router.types import HistoryEntry, SemanticRouterResponse
from top_assist.slack.messages import (
    ask_for_feedback,
    mark_message_as_acknowledged,
    post_answer_on_slack,
    post_channel_is_not_enabled,
)
from top_assist.utils.metrics import (
    ANSWER_LATENCY_HISTOGRAM_METRIC,
    ANSWER_LATENCY_SUMMARY_METRIC,
    EVENT_LATENCY_HISTOGRAM_METRIC,
    EVENT_LATENCY_SUMMARY_METRIC,
    QUESTION_ASKED_METRIC,
)
from top_assist.utils.scheduler import call_with_delay
from top_assist.utils.sentry_notifier import sentry_notify_exception
from top_assist.utils.tracer import ServiceNames, tracer


class QuestionEvent(BaseModel):
    """Question event received from Slack.

    Attr:
        text: The text of the message
        ts: The timestamp of the message
        thread_ts: The thread timestamp of the message
        channel: The channel ID where the message was posted
        is_dm: Whether the question was asked in a direct message
        user: The Slack user ID of the user who asked the question
    """

    text: str
    ts: str
    thread_ts: str | None
    channel: str
    is_dm: bool
    user: str

    def is_follow_up(self) -> bool:
        return self.thread_ts is not None


class UnknownInteractionError(Exception):  # noqa: D101
    def __init__(self, thread_id: str):
        super().__init__(f"Feedback received for non-existent interaction: {thread_id}")


@tracer.wrap(resource="process_question", service=ServiceNames.chat_bot.value)
def process_question(question: QuestionEvent) -> None:
    try:
        if not question.is_dm and not slack_reply_questions_in_channels:
            post_channel_is_not_enabled(channel=question.channel, thread_ts=question.thread_ts or question.ts)
            return

        with authorize_for(question.user, question) as policy:
            __process_question(question, policy)

    except UnauthenticatedUserError:
        logging.info("User is not authenticated", extra={"slack_user_id": question.user})
        return

    except Exception as e:
        logging.exception("Error occurred", extra={"error": str(e), "event": question})
        sentry_notify_exception(e)


def __process_question(question: QuestionEvent, policy: PageAccessPolicy) -> None:
    logging.info("Processing question", extra={"slack_user_id": question.user, "channel": question.channel})
    latency_checkpoint_ts = datetime.now(UTC)

    mark_message_as_acknowledged(question.channel, question.ts)
    __track_event_latency(question, latency_checkpoint_ts)
    __send_question_asked_metric(question)

    interaction = __upsert_interaction(question)
    completion = __process_query(interaction, policy)

    __store_answer(question, interaction, completion)
    __post_answer_on_slack(question, completion.message)
    __track_answer_latency(question, latency_checkpoint_ts)

    __mark_answer_posted_on_slack(question, interaction)
    __ask_feedback(question)


def __upsert_interaction(question: QuestionEvent) -> QAInteractionDTO:
    if question.thread_ts:
        interaction = db_interactions.find_by_thread_id(question.thread_ts)
        if not interaction:
            raise UnknownInteractionError(question.thread_ts)

        db_interactions.append_comment(
            interaction,
            text=question.text,
            author_slack_user_id=question.user,
            timestamp=datetime.fromtimestamp(float(question.ts), UTC),
        )
    else:
        interaction = db_interactions.add_question(
            question=question.text,
            question_timestamp=datetime.fromtimestamp(float(question.ts), UTC),
            thread_id=question.ts,
            channel_id=question.channel,
            slack_user_id=question.user,
        )

    return interaction


def __process_query(
    interaction: QAInteractionDTO,
    policy: PageAccessPolicy,
) -> SemanticRouterResponse:
    return route_with_semantic_router(
        history=__restore_thread_history(interaction),
        policy=policy,
        assistant_thread_id=interaction.assistant_thread_id,
    )


def __store_answer(question: QuestionEvent, interaction: QAInteractionDTO, completion: SemanticRouterResponse) -> None:
    if question.is_follow_up():
        db_interactions.append_comment_answer(
            interaction, answer=completion.message, comment_timestamp=datetime.fromtimestamp(float(question.ts), UTC)
        )
    else:
        db_interactions.add_answer(
            interaction,
            answer=completion.message,
            assistant_thread_id=completion.assistant_thread_id,
        )


def __post_answer_on_slack(question: QuestionEvent, response_text: str) -> None:
    post_answer_on_slack(
        response_text,
        channel=question.channel,
        thread_ts=question.thread_ts or question.ts,
    )
    logging.info("Answer posted on Slack thread", extra={"ts": question.ts})


def __mark_answer_posted_on_slack(question: QuestionEvent, interaction: QAInteractionDTO) -> None:
    if question.is_follow_up():
        db_interactions.mark_comment_answer_posted_on_slack(
            interaction, comment_timestamp=datetime.fromtimestamp(float(question.ts), UTC)
        )
    else:
        db_interactions.mark_answer_posted_on_slack(interaction)


def __restore_thread_history(interaction: QAInteractionDTO) -> list[HistoryEntry]:
    history: list[HistoryEntry] = [{"role": "user", "content": interaction.question_text}]

    if interaction.answer_text:
        history.append({"role": "assistant", "content": interaction.answer_text})

    if interaction.comments:
        parsed_comments = json.loads(interaction.comments)
        for comment in parsed_comments:
            if comment.get("text"):
                history.append({"role": "user", "content": comment["text"]})
            if comment.get("assistant_response"):
                history.append({"role": "assistant", "content": comment["assistant_response"]})

    return history


def __send_question_asked_metric(question: QuestionEvent) -> None:
    if question.is_follow_up():
        return

    QUESTION_ASKED_METRIC.labels(user=question.user).inc()


def __track_answer_latency(question: QuestionEvent, start_ts: datetime) -> None:
    latency = datetime.now(UTC) - start_ts
    question_type = "follow_up" if question.is_follow_up() else "question"
    logging.info(
        "Answer posted",
        extra={
            "type": question_type,
            "slack_user_id": question.user,
            "channel": question.channel,
            "latency_seconds": latency.total_seconds(),
        },
    )
    ANSWER_LATENCY_HISTOGRAM_METRIC.labels(type=question_type).observe(latency.total_seconds())
    ANSWER_LATENCY_SUMMARY_METRIC.labels(type=question_type).observe(latency.total_seconds())


def __track_event_latency(question: QuestionEvent, event_received_ts: datetime) -> None:
    latency = event_received_ts - datetime.fromtimestamp(float(question.ts), UTC)
    question_type = "follow_up" if question.is_follow_up() else "question"

    logging.info(
        "Chat bot event received",
        extra={
            "type": question_type,
            "slack_user_id": question.user,
            "channel": question.channel,
            "latency_seconds": latency.total_seconds(),
        },
    )
    EVENT_LATENCY_HISTOGRAM_METRIC.labels(type=question_type).observe(latency.total_seconds())
    EVENT_LATENCY_SUMMARY_METRIC.labels(type=question_type).observe(latency.total_seconds())


def __ask_feedback(question: QuestionEvent) -> None:
    if question.is_follow_up():
        return

    # Ephemeral messages are delivered to clients faster than normal messages, let's delay the process a bit to ensure the proper order
    call_with_delay(
        timedelta(seconds=2),
        lambda: ask_for_feedback(channel=question.channel, thread_ts=question.ts, slack_user_id=question.user),
    )
