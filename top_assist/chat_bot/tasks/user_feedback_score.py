import logging

import top_assist.database.interactions as db_interactions
import top_assist.database.user_feedback_scores as db_user_feedback_scores
from top_assist.slack.bot_runner import SlackBotBlockActionTriggered
from top_assist.slack.messages import is_feedback_action_positive, mark_feedback_received
from top_assist.utils.metrics import ANSWER_USER_FEEDBACK_NEGATIVE_METRIC, ANSWER_USER_FEEDBACK_POSITIVE_METRIC
from top_assist.utils.tracer import ServiceNames, tracer


@tracer.wrap(resource="process_user_feedback_score", service=ServiceNames.chat_bot.value)
def process_user_feedback_score(block_action: SlackBotBlockActionTriggered) -> None:
    logging.info(
        "Processing user_feedback_score started", extra={"user": block_action.user, "channel": block_action.channel}
    )

    if not block_action.thread_ts:
        return

    interaction = db_interactions.find_by_thread_id(block_action.thread_ts)
    if not interaction:
        logging.warning(
            "Interaction not found for the thread",
            extra={"thread_ts": block_action.thread_ts},
        )
        return

    positive = is_feedback_action_positive(block_action)

    db_user_feedback_scores.add(
        slack_user_id=block_action.user,
        channel_id=block_action.channel,
        thread_id=block_action.thread_ts,
        positive=positive,
    )
    mark_feedback_received(response_url=block_action.response_url, thread_ts=block_action.thread_ts)

    metric = ANSWER_USER_FEEDBACK_POSITIVE_METRIC if positive else ANSWER_USER_FEEDBACK_NEGATIVE_METRIC
    metric.inc()
