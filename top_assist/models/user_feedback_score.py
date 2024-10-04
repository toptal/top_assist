from .base import Base, Mapped, int_pk, thread_id


class UserFeedbackScoreORM(Base):
    """SQLAlchemy model for storing user feedback scores for top-assist answers.

    Attr:
        id: The primary key of the user feedback score.
        slack_user_id: The Slack user ID.
        channel_id: The Slack channel ID.
        thread_id: The Slack thread ID.
        positive: Whether the feedback is positive
    """

    __tablename__ = "user_feedback_scores"

    id: Mapped[int_pk]
    slack_user_id: Mapped[str]
    channel_id: Mapped[str]
    thread_id: Mapped[thread_id]
    positive: Mapped[bool]
