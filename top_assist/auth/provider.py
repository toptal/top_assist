import logging
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

import top_assist.database.user_auth as db_user_auth
from top_assist.configuration import (
    cryptography_secret_key,
)
from top_assist.confluence.oauth import tokens_with_refresh_token
from top_assist.confluence.policy import InvalidAuthError, PageAccessPolicy
from top_assist.utils.cypher import Cypher

from ._sign_in_context import sign_in_context_from_operation
from ._sign_in_context import validate_operation_class as _validate_operation_class
from .sign_in_flow import start_sign_in_flow


class UnauthenticatedUserError(Exception):  # noqa: D101
    pass


@contextmanager
def authorize_for(slack_user_id: str, operation: BaseModel) -> Generator[PageAccessPolicy, None, None]:
    _validate_operation_class(type(operation))

    confluence_access_token = __authenticate(slack_user_id)

    if confluence_access_token is None:
        logging.info("User is not authenticated", extra={"slack_user_id": slack_user_id})
        start_sign_in_flow(sign_in_context_from_operation(slack_user_id, operation))
        raise UnauthenticatedUserError

    policy = PageAccessPolicy(slack_user_id=slack_user_id, confluence_access_token=confluence_access_token)

    try:
        yield policy

    except InvalidAuthError:
        db_user_auth.delete_by_slack_id(slack_user_id)
        start_sign_in_flow(sign_in_context_from_operation(slack_user_id, operation))
        raise


def __authenticate(slack_user_id: str) -> str | None:
    user = db_user_auth.find_by_slack_id(slack_user_id)

    if not user or not user.access_token or not user.refresh_token:
        return None

    if not user.access_token_expires_at or user.access_token_expires_at < datetime.now(UTC):
        logging.info("Access Token expired, refreshing it", extra={"slack_user_id": slack_user_id})
        return __refresh_oauth_tokens(slack_user_id=slack_user_id, refresh_token=_cypher.decrypt(user.refresh_token))

    return _cypher.decrypt(user.access_token)


def __refresh_oauth_tokens(*, slack_user_id: str, refresh_token: str) -> str | None:
    try:
        tokens = tokens_with_refresh_token(refresh_token)
        db_user_auth.update_tokens(
            slack_user_id=slack_user_id,
            access_token=_cypher.encrypt(tokens.access_token),
            refresh_token=_cypher.encrypt(tokens.refresh_token),
            expires_in=timedelta(seconds=tokens.expires_in),
        )

        return tokens.access_token

    except Exception as e:
        logging.exception("Error refreshing token", extra={"slack_user_id": slack_user_id, "error": e})
        return None


_cypher = Cypher(secret_key=cryptography_secret_key)
