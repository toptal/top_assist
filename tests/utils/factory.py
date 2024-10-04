from datetime import UTC, datetime

from top_assist.database.database import get_db_session
from top_assist.models.channel import ChannelDTO, ChannelORM
from top_assist.models.qa_interaction import QAInteractionDTO, QAInteractionORM


def create_interaction_question(
    question: str = "What's up",
    question_timestamp: datetime | None = None,
    thread_id: str = "fake_thread_id",
    channel_id: str = "fake_channel_id",
    slack_user_id: str = "fake_slack_user_id",
) -> QAInteractionDTO:
    if not question_timestamp:
        question_timestamp = datetime.now(tz=UTC)

    with get_db_session() as session:
        interaction = QAInteractionORM(
            question_text=question,
            question_timestamp=question_timestamp,
            thread_id=thread_id,
            channel_id=channel_id,
            slack_user_id=slack_user_id,
        )
        session.add(interaction)
        session.flush()
        return QAInteractionDTO.from_orm(interaction)


def create_channel(slack_channel_id: str = "fake_slack_channel_id", name: str = "fake_name") -> ChannelDTO:
    with get_db_session() as session:
        channel = ChannelORM(slack_channel_id=slack_channel_id, name=name)
        session.add(channel)
        session.flush()
        return ChannelDTO.from_orm(channel)
