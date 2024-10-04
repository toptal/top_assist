import typing

from pydantic import BaseModel

from .base import Base, Index, Mapped, Optional, int_pk, thread_id, timestamp


class QAInteractionORM(Base):
    """SQLAlchemy model for storing QA interactions.

    Attr:
        id: The primary key of the QA interaction.
        question_text: The question text.
        channel_id: The Slack channel ID.
        thread_id: The Slack thread ID.
        slack_user_id: The Slack user ID.
        question_timestamp: The timestamp when the question was asked.
        assistant_thread_id: ChatGPT assistant thread ID.
        answer_text: The answer text.
        answer_timestamp: The timestamp when the answer was saved.
        answer_posted_on_slack: The timestamp when the answer was posted on Slack.
        comments: Additional interactions (follow-up questions) in the current Slack thread.
    """

    __tablename__ = "qa_interactions"

    id: Mapped[int_pk]
    question_text: Mapped[str]
    channel_id: Mapped[str]
    thread_id: Mapped[thread_id]
    slack_user_id: Mapped[str]
    question_timestamp: Mapped[timestamp]
    assistant_thread_id: Mapped[Optional[str]]
    answer_text: Mapped[Optional[str]]
    answer_timestamp: Mapped[Optional[timestamp]]
    answer_posted_on_slack: Mapped[Optional[timestamp]]
    comments: Mapped[Optional[str]]

    repr_cols = ("thread_id", "channel_id", "slack_user_id")

    __table_args__ = (Index("ix_qa_interactions_thread_id", "thread_id"),)


class QAInteractionDTO(BaseModel):
    """Data transfer object for QAInteractionORM.

    Attr:
        interaction_id: The primary key of the QA interaction.
        question_text: The question text.
        channel_id: The Slack channel ID.
        slack_thread_id: The Slack thread ID.
        slack_user_id: The Slack user ID.
        answer_text: The answer text.
        assistant_thread_id: ChatGPT assistant thread ID.
        comments: Additional interactions (follow-up questions) in the current Slack thread.
    """

    interaction_id: int_pk
    question_text: str
    channel_id: str
    slack_thread_id: str
    slack_user_id: str
    answer_text: str | None
    assistant_thread_id: str | None
    comments: str | None

    @classmethod
    def from_orm(cls, model: QAInteractionORM) -> typing.Self:
        return cls(
            interaction_id=model.id,
            question_text=model.question_text,
            channel_id=model.channel_id,
            slack_thread_id=model.thread_id,
            slack_user_id=model.slack_user_id,
            answer_text=model.answer_text,
            assistant_thread_id=model.assistant_thread_id,
            comments=model.comments,
        )
