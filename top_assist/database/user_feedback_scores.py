import logging

from top_assist.models.user_feedback_score import UserFeedbackScoreORM

from .database import get_db_session


def add(
    *,
    slack_user_id: str,
    channel_id: str,
    thread_id: str,
    positive: bool,
) -> None:
    """Registers user Feedback score for a given answer."""
    with get_db_session() as session:
        user_feedback_score = UserFeedbackScoreORM(
            slack_user_id=slack_user_id,
            channel_id=channel_id,
            thread_id=thread_id,
            positive=positive,
        )
        session.add(user_feedback_score)

        logging.info("User feedback score registered", extra={"user": slack_user_id, "positive": positive})
