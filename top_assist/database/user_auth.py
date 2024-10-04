from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from top_assist.models.base import int_pk
from top_assist.models.user_auth import UserAuthDTO, UserAuthORM

from .database import get_db_session


class UserAuthNotFoundError(Exception):  # noqa: D101
    pass


def find_by_id(auth_id: int) -> UserAuthDTO | None:
    with get_db_session() as session:
        user_auth = session.get(UserAuthORM, auth_id)
        return UserAuthDTO.from_orm(user_auth) if user_auth else None


def find_by_slack_id(slack_user_id: str) -> UserAuthDTO | None:
    with get_db_session() as session:
        user_auth = session.query(UserAuthORM).filter_by(slack_user_id=slack_user_id).first()
        return UserAuthDTO.from_orm(user_auth) if user_auth else None


@dataclass
class RequestUpsertResult:
    """Stores the old auth message ID for the user. It is used to delete the old message when the user starts a new auth process."""

    old_auth_message_id: str | None


def upsert_request(*, slack_user_id: str, encrypted_state: str, auth_message_id: str) -> RequestUpsertResult:
    with get_db_session() as session:
        user_auth_orm = session.query(UserAuthORM).filter_by(slack_user_id=slack_user_id).first()
        if user_auth_orm:
            user_auth_orm.state = encrypted_state
            old_auth_message_id = user_auth_orm.auth_message_id
            user_auth_orm.auth_message_id = auth_message_id
            return RequestUpsertResult(old_auth_message_id=old_auth_message_id)
        else:
            user_auth = UserAuthORM(
                slack_user_id=slack_user_id,
                state=encrypted_state,
                auth_message_id=auth_message_id,
            )
            session.add(user_auth)
            return RequestUpsertResult(old_auth_message_id=None)


@dataclass
class RequestCompletionResult:
    """Stores the old auth message ID for the user. It is used to delete the message after the user has completed the auth process."""

    old_auth_message_id: str


def complete_request(
    *,
    slack_user_id: str,
    access_token: str,
    refresh_token: str,
    expires_in: timedelta,
) -> RequestCompletionResult:
    with get_db_session() as session:
        user_auth_orm = session.query(UserAuthORM).filter_by(slack_user_id=slack_user_id).first()
        if not user_auth_orm:
            raise UserAuthNotFoundError

        if not user_auth_orm.state or not user_auth_orm.auth_message_id:
            raise AssertionError

        __update_tokens(user_auth_orm, access_token, refresh_token, expires_in)

        user_auth_orm.state = None
        old_auth_message_id = user_auth_orm.auth_message_id
        user_auth_orm.auth_message_id = None
        return RequestCompletionResult(old_auth_message_id=old_auth_message_id)


def update_tokens(
    *,
    slack_user_id: str,
    access_token: str,
    refresh_token: str,
    expires_in: timedelta,
) -> None:
    with get_db_session() as session:
        user_auth_orm = session.query(UserAuthORM).filter_by(slack_user_id=slack_user_id).first()
        if not user_auth_orm:
            raise UserAuthNotFoundError

        if user_auth_orm.auth_message_id or user_auth_orm.state:
            raise AssertionError

        __update_tokens(user_auth_orm, access_token, refresh_token, expires_in)


def __update_tokens(orm: UserAuthORM, access_token: str, refresh_token: str, expires_in: timedelta) -> None:
    orm.access_token = access_token
    orm.refresh_token = refresh_token
    orm.access_token_expires_at = datetime.now(UTC) + expires_in - timedelta(minutes=5)  # subtract 5 minutes to be safe


def delete_by_id(auth_id: int_pk) -> None:
    with get_db_session() as session:
        user_auth = session.get(UserAuthORM, auth_id)
        if not user_auth:
            raise UserAuthNotFoundError

        session.delete(user_auth)


def delete_by_slack_id(slack_user_id: str) -> None:
    with get_db_session() as session:
        user_auth = session.query(UserAuthORM).filter_by(slack_user_id=slack_user_id).first()
        if not user_auth:
            raise UserAuthNotFoundError

        session.delete(user_auth)
