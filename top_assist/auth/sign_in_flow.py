import logging
from dataclasses import dataclass
from datetime import timedelta

from top_assist.configuration import (
    confluence_oauth_top_assist_redirect_url_template,
    cryptography_secret_key,
)
from top_assist.confluence.oauth import generate_confluence_oauth_link, tokens_from_oauth_code
from top_assist.confluence.profile import fetch_confluence_email
from top_assist.database import user_auth as db_user_auth
from top_assist.slack.messages import delete_message, send_confluence_auth_link
from top_assist.slack.profile import fetch_slack_email
from top_assist.utils.cypher import Cypher
from top_assist.utils.sentry_notifier import sentry_notify_issue

from ._sign_in_context import (
    AuthCallback,
    ExpiredAuthState,
    SignInContext,
    parse_auth_request_state,
    register_sign_in_context_operation,  # noqa: F401 imported to export
)


def start_sign_in_flow(context: SignInContext) -> None:
    top_assist_auth_url = confluence_oauth_top_assist_redirect_url_template.format(state=context.encrypted_state)
    slack_message = send_confluence_auth_link(context.slack_user_id, top_assist_auth_url)

    result = db_user_auth.upsert_request(
        slack_user_id=context.slack_user_id,
        encrypted_state=context.encrypted_state,
        auth_message_id=slack_message.ts,
    )
    if result.old_auth_message_id:
        delete_message(ts=result.old_auth_message_id, channel=context.slack_user_id)

    logging.info("Confluence auth link sent to user", extra={"slack_user_id": context.slack_user_id})


def generate_provider_oauth_link(*, state: str) -> str:
    return generate_confluence_oauth_link(state=state)


@dataclass
class SignInCompleted:  # noqa: D101
    pending_operation: AuthCallback


@dataclass
class AlreadySignedIn:  # noqa: D101
    pass


@dataclass
class SignInLinkExpired:  # noqa: D101
    context_for_retry: SignInContext


@dataclass
class EmailMismatch:  # noqa: D101
    pass


class InvalidAuthStateError(ValueError):  # noqa: D101
    pass


def process_confluence_oauth_callback(
    *, encrypted_state: str, code: str
) -> SignInCompleted | AlreadySignedIn | SignInLinkExpired | EmailMismatch:
    state = parse_auth_request_state(encrypted_state)
    db_state = db_user_auth.find_by_slack_id(state.slack_user_id)

    if db_state and db_state.access_token and db_state.refresh_token:
        return AlreadySignedIn()

    if isinstance(state, ExpiredAuthState):
        return SignInLinkExpired(state.state_for_retry)

    if not db_state or db_state.state != encrypted_state:
        logging.error(
            "Received confluence oauth code with unexpected state",
            extra={
                "slack_user_id": state.slack_user_id,
                "received_state": encrypted_state,
                "has_saved_state": bool(db_state),
                "saved_state": db_state and db_state.state,
            },
        )
        raise InvalidAuthStateError

    tokens = tokens_from_oauth_code(code)
    try:
        confluence_info = fetch_confluence_email(user_access_token=tokens.access_token)
    except Exception:
        logging.exception("Failed to fetch Confluence email", extra={"slack_user_id": state.slack_user_id})
        raise

    try:
        slack_info = fetch_slack_email(slack_user_id=state.slack_user_id)
    except Exception:
        logging.exception("Failed to fetch Slack email", extra={"slack_user_id": state.slack_user_id})
        raise

    # purely informative, not a required security check
    if not confluence_info.is_email_verified:
        sentry_notify_issue(
            "Email not verified",
            extra={
                "confluence_email": confluence_info.email,
                "confluence_email_verified": confluence_info.is_email_verified,
                "slack_user_id": state.slack_user_id,
            },
        )

    if confluence_info.email != slack_info.email:
        extra = {
            "slack_email": slack_info,
            "confluence_email": confluence_info,
            "slack_user_id": state.slack_user_id,
        }
        logging.exception("Email mismatch detected", extra=extra)
        sentry_notify_issue("Email mismatch detected", extra=extra)
        return EmailMismatch()

    result = db_user_auth.complete_request(
        slack_user_id=state.slack_user_id,
        access_token=_cypher.encrypt(tokens.access_token),
        refresh_token=_cypher.encrypt(tokens.refresh_token),
        expires_in=timedelta(seconds=tokens.expires_in),
    )
    delete_message(channel=state.slack_user_id, ts=result.old_auth_message_id)

    return SignInCompleted(pending_operation=state.resume_operation)


_cypher = Cypher(secret_key=cryptography_secret_key)
