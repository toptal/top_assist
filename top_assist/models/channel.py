import typing

from pydantic import BaseModel

from .base import Base, Mapped, int_pk, unique_string


class ChannelORM(Base):
    """SQLAlchemy model for storing Slack Channels.

    Attr:
        id: The primary key of the channel.
        slack_channel_id: The Slack channel ID.
        name: The Slack channel name.
    """

    __tablename__ = "channels"

    id: Mapped[int_pk]
    slack_channel_id: Mapped[unique_string]
    name: Mapped[str]


class ChannelDTO(BaseModel):
    """Data transfer object for ChannelORM.

    Attr:
        id: The primary key of the channel.
        slack_channel_id: The Slack channel ID.
        name: The Slack channel name.
    """

    id: int_pk
    slack_channel_id: str
    name: str

    @classmethod
    def from_orm(cls, model: ChannelORM) -> typing.Self:
        return cls(
            id=model.id,
            slack_channel_id=model.slack_channel_id,
            name=model.name,
        )
