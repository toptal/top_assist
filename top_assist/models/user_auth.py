import typing

from pydantic import BaseModel

from .base import Base, Mapped, Optional, int_pk, timestamp, unique_string


class UserAuthORM(Base):
    """SQLAlchemy model for storing users.

    Attr:
        id: The primary key of the user.
        slack_user_id: The Slack user ID.
        access_token: Confluence access token.
        access_token_expires_at: The timestamp when the access token expires.
        refresh_token: Confluence refresh token.
        state: The state used for OAuth.
        auth_message_id: The Slack message ID used for OAuth link.
    """

    __tablename__ = "user_auth"

    id: Mapped[int_pk]
    slack_user_id: Mapped[unique_string]
    access_token: Mapped[Optional[str]]
    access_token_expires_at: Mapped[Optional[timestamp]]
    refresh_token: Mapped[Optional[str]]
    state: Mapped[Optional[str]]
    auth_message_id: Mapped[Optional[str]]

    repr_cols_num = 2


class UserAuthDTO(BaseModel):
    """Data transfer object for UserAuthORM.

    Attr:
        id: The primary key of the user.
        slack_user_id: The Slack user ID.
        access_token: Confluence access token.
        access_token_expires_at: The timestamp when the access token expires.
        refresh_token: Confluence refresh token.
        state: The state used for OAuth.
        auth_message_id: The Slack message ID used for OAuth link.
    """

    id: int_pk
    slack_user_id: str
    access_token: str | None
    access_token_expires_at: timestamp | None
    refresh_token: str | None
    state: str | None
    auth_message_id: str | None

    @classmethod
    def from_orm(cls, model: UserAuthORM) -> typing.Self:
        return cls(
            id=model.id,
            slack_user_id=model.slack_user_id,
            access_token=model.access_token,
            access_token_expires_at=model.access_token_expires_at,
            refresh_token=model.refresh_token,
            state=model.state,
            auth_message_id=model.auth_message_id,
        )
