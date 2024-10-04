from top_assist.models.channel import ChannelDTO, ChannelORM

from .database import get_db_session


def find_by_id(channel_id: int) -> ChannelDTO | None:
    with get_db_session() as session:
        record = session.get(ChannelORM, channel_id)

        return ChannelDTO.from_orm(record) if record else None


def upsert(slack_channel_id: str, name: str) -> None:
    with get_db_session() as session:
        channel = session.query(ChannelORM).filter(ChannelORM.slack_channel_id == slack_channel_id).first()
        if channel:
            channel.name = name
        else:
            channel = ChannelORM(slack_channel_id=slack_channel_id, name=name)
            session.add(channel)


def delete_by_id(channel_id: int) -> None:
    with get_db_session() as session:
        channel = session.get(ChannelORM, channel_id)
        if channel:
            session.delete(channel)


def delete_by_slack_channel_id(slack_channel_id: str) -> None:
    with get_db_session() as session:
        channel = session.query(ChannelORM).filter(ChannelORM.slack_channel_id == slack_channel_id).first()
        if channel:
            session.delete(channel)
