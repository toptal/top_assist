import json
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from freezegun import freeze_time

from top_assist.auth.sign_in_flow import (
    AlreadySignedIn,
    EmailMismatch,
    InvalidAuthStateError,
    SignInCompleted,
    SignInLinkExpired,
    process_confluence_oauth_callback,
)
from top_assist.chat_bot.tasks.question import QuestionEvent, process_question
from top_assist.confluence.oauth import ConfluenceOAuthTokens
from top_assist.confluence.profile import ConfluenceUserEmail
from top_assist.database.user_auth import RequestCompletionResult
from top_assist.models.user_auth import UserAuthDTO
from top_assist.slack.profile import SlackUserEmail


def build_raw_state(expires_at: datetime | None = None, serialized_operation: str | None = None) -> dict:
    return {
        "expires_at": (expires_at or (datetime.now(UTC) + timedelta(seconds=3600))).isoformat(),
        "slack_user_id": "U123456",
        "operation": (
            serialized_operation
            or json.dumps({
                "text": "test_text",
                "ts": "test_ts",
                "thread_ts": "thread_ts",
                "channel": "test_channel",
                "is_dm": True,
                "user": "U123456",
                "__class": "QuestionEvent",
            })
        ),
    }


def build_encrypted_state(expires_at: datetime | None = None, serialized_operation: str | None = None) -> str:
    return "fake_encrypted_" + json.dumps(
        build_raw_state(expires_at=expires_at, serialized_operation=serialized_operation)
    )


@pytest.fixture(autouse=True)
def _auto_mocked_tokens_from_oauth_code() -> Generator:
    with patch("top_assist.auth.sign_in_flow.tokens_from_oauth_code", autospec=True) as mock:
        mock.return_value = ConfluenceOAuthTokens(
            access_token="access_token_from_oauth_code",
            refresh_token="refresh_token_from_oauth_code",
            expires_in=3600,
        )
        yield


@pytest.fixture()
def mocked_slack_email() -> Generator[MagicMock, None, None]:
    with patch("top_assist.auth.sign_in_flow.fetch_slack_email", autospec=True) as mock:
        value = SlackUserEmail(email="test@example.com", is_email_confirmed=True)
        mock.return_value = value
        yield mock


@pytest.fixture()
def mocked_confluence_email() -> Generator[MagicMock, None, None]:
    with patch("top_assist.auth.sign_in_flow.fetch_confluence_email", autospec=True) as mock:
        value = ConfluenceUserEmail(email="test@example.com", is_email_verified=True)
        mock.return_value = value
        yield mock


# Subclass is used to have state present (as opposed to optional in UserAuthDTO)
class UserWithSignInRequest(UserAuthDTO):
    state: str
    auth_message_id: str


@pytest.fixture()
def mocked_user_with_sign_in_request() -> Generator[UserWithSignInRequest, None, None]:
    with patch("top_assist.auth.sign_in_flow.db_user_auth.find_by_slack_id", autospec=True) as mock:
        value = UserWithSignInRequest(
            id=-1,
            slack_user_id="U123456",
            access_token=None,
            access_token_expires_at=None,
            refresh_token=None,
            state=build_encrypted_state(),
            auth_message_id="test_message_id",
        )
        mock.return_value = value
        yield value


@pytest.fixture()
def mocked_user_with_completed_sign_in() -> Generator[UserAuthDTO, None, None]:
    with patch("top_assist.auth.sign_in_flow.db_user_auth.find_by_slack_id", autospec=True) as mock:
        value = UserAuthDTO(
            id=-1,
            slack_user_id="U123456",
            access_token="fake_encrypted_access_token",
            access_token_expires_at=datetime.now(UTC) + timedelta(seconds=3600),
            refresh_token="fake_encrypted_refresh_token",
            state=None,
            auth_message_id=None,
        )
        mock.return_value = value
        yield value


@pytest.fixture()
def mocked_user_without_auth_record() -> Generator[None, None, None]:
    with patch("top_assist.auth.sign_in_flow.db_user_auth.find_by_slack_id", autospec=True) as mock:
        value = None
        mock.return_value = value
        yield value


@patch("top_assist.auth.sign_in_flow.db_user_auth.complete_request", autospec=True)
@patch("top_assist.auth.sign_in_flow.delete_message", autospec=True)
def test_process_confluence_oauth_callback_success(
    mock_delete_message: MagicMock,
    mock_complete_request: MagicMock,
    mocked_user_with_sign_in_request: UserWithSignInRequest,
    mocked_confluence_email: MagicMock,  # noqa: ARG001
    mocked_slack_email: MagicMock,  # noqa: ARG001
) -> None:
    # Given
    mock_complete_request.return_value = Mock(RequestCompletionResult, old_auth_message_id="old_auth_message_id")

    # When
    result = process_confluence_oauth_callback(
        encrypted_state=mocked_user_with_sign_in_request.state,
        code="test_code",
    )

    # Then
    assert isinstance(result, SignInCompleted)
    assert result.pending_operation.function == process_question
    assert result.pending_operation.arg == QuestionEvent(
        text="test_text",
        ts="test_ts",
        thread_ts="thread_ts",
        channel="test_channel",
        is_dm=True,
        user="U123456",
    )
    mock_complete_request.assert_called_once_with(
        slack_user_id="U123456",
        access_token="fake_encrypted_access_token_from_oauth_code",
        refresh_token="fake_encrypted_refresh_token_from_oauth_code",
        expires_in=timedelta(seconds=3600),
    )
    mock_delete_message.assert_called_once_with(channel="U123456", ts="old_auth_message_id")


@patch("top_assist.auth.sign_in_flow.db_user_auth.complete_request", autospec=True)
@patch("top_assist.auth.sign_in_flow.delete_message", autospec=True)
@patch("top_assist.auth.sign_in_flow.sentry_notify_issue", autospec=True)
def test_process_confluence_oauth_callback_success_with_unverified_confluence_email(
    mock_sentry_notify_issue: MagicMock,
    mock_delete_message: MagicMock,
    mock_complete_request: MagicMock,
    mocked_user_with_sign_in_request: UserWithSignInRequest,
    mocked_confluence_email: MagicMock,
    mocked_slack_email: MagicMock,  # noqa: ARG001
) -> None:
    # Given
    mocked_confluence_email.return_value.is_email_verified = False
    mock_complete_request.return_value = Mock(RequestCompletionResult, old_auth_message_id="old_auth_message_id")

    # When
    result = process_confluence_oauth_callback(
        encrypted_state=mocked_user_with_sign_in_request.state,
        code="test_code",
    )

    # Then
    assert isinstance(result, SignInCompleted)
    assert result.pending_operation.function == process_question
    assert result.pending_operation.arg == QuestionEvent(
        text="test_text",
        ts="test_ts",
        thread_ts="thread_ts",
        channel="test_channel",
        is_dm=True,
        user="U123456",
    )
    mock_complete_request.assert_called_once_with(
        slack_user_id="U123456",
        access_token="fake_encrypted_access_token_from_oauth_code",
        refresh_token="fake_encrypted_refresh_token_from_oauth_code",
        expires_in=timedelta(seconds=3600),
    )
    mock_delete_message.assert_called_once_with(channel="U123456", ts="old_auth_message_id")
    mock_sentry_notify_issue.assert_called_once_with(
        "Email not verified",
        extra={
            "confluence_email": "test@example.com",
            "confluence_email_verified": False,
            "slack_user_id": "U123456",
        },
    )


@patch("top_assist.auth.sign_in_flow.db_user_auth.complete_request", autospec=True)
@patch("top_assist.auth.sign_in_flow.delete_message", autospec=True)
def test_process_confluence_oauth_callback_success_with_corrupted_operation(
    mock_delete_message: MagicMock,
    mock_complete_request: MagicMock,
    mocked_user_with_sign_in_request: UserWithSignInRequest,
    mocked_confluence_email: MagicMock,  # noqa: ARG001
    mocked_slack_email: MagicMock,  # noqa: ARG001
) -> None:
    # Given
    encrypted_state = build_encrypted_state(serialized_operation="corrupted_operation")
    mocked_user_with_sign_in_request.state = encrypted_state
    mock_complete_request.return_value = Mock(RequestCompletionResult, old_auth_message_id="old_auth_message_id")

    # When
    result = process_confluence_oauth_callback(encrypted_state=encrypted_state, code="test_code")

    # Then
    assert isinstance(result, SignInCompleted)
    assert callable(result.pending_operation.function)
    assert result.pending_operation.arg is None
    mock_complete_request.assert_called_once_with(
        slack_user_id="U123456",
        access_token="fake_encrypted_access_token_from_oauth_code",
        refresh_token="fake_encrypted_refresh_token_from_oauth_code",
        expires_in=timedelta(seconds=3600),
    )
    mock_delete_message.assert_called_once_with(channel="U123456", ts="old_auth_message_id")


def test_process_confluence_oauth_callback_with_signed_in_user(
    mocked_user_with_completed_sign_in: UserAuthDTO,  # noqa: ARG001
) -> None:
    # Given
    encrypted_state = build_encrypted_state()

    # When
    result = process_confluence_oauth_callback(encrypted_state=encrypted_state, code="test_code")

    # Then
    assert result == AlreadySignedIn()


@freeze_time("2021-10-01T00:00:00+00:00")
def test_process_confluence_oauth_callback_with_expired_state(
    mocked_user_with_sign_in_request: UserWithSignInRequest,
) -> None:
    # Given
    now_time = datetime.now(UTC)
    expired_state_time = now_time - timedelta(days=1)
    refreshed_state_time = now_time + timedelta(minutes=5)
    encrypted_state = build_encrypted_state(expires_at=expired_state_time)

    mocked_user_with_sign_in_request.state = encrypted_state

    # When
    result = process_confluence_oauth_callback(encrypted_state=encrypted_state, code="test_code")

    # Then
    assert isinstance(result, SignInLinkExpired)
    assert result.context_for_retry.slack_user_id == "U123456"
    assert result.context_for_retry.encrypted_state.startswith("fake_encrypted_")
    assert json.loads(result.context_for_retry.encrypted_state.removeprefix("fake_encrypted_")) == build_raw_state(
        expires_at=refreshed_state_time
    )


def test_process_confluence_oauth_callback_with_user_having_no_auth_record(
    mocked_user_without_auth_record: None,  # noqa: ARG001
) -> None:
    # Given
    encrypted_state = build_encrypted_state()

    # When
    with pytest.raises(InvalidAuthStateError) as exc_info:
        process_confluence_oauth_callback(encrypted_state=encrypted_state, code="test_code")

    # Then
    assert exc_info


def test_process_confluence_oauth_callback_with_invalid_state(
    mocked_user_with_sign_in_request: UserWithSignInRequest,
) -> None:
    # Given
    encrypted_state = build_encrypted_state()

    mocked_user_with_sign_in_request.state = "fake_encrypted_different_state"

    # When
    with pytest.raises(InvalidAuthStateError) as exc_info:
        process_confluence_oauth_callback(encrypted_state=encrypted_state, code="test_code")

    # Then
    assert exc_info


def test_process_confluence_oauth_callback_with_email_mismatch(
    mocked_user_with_sign_in_request: UserWithSignInRequest,
    mocked_confluence_email: MagicMock,
    mocked_slack_email: MagicMock,
) -> None:
    # Given
    mocked_confluence_email.return_value.email = "test1@example.com"
    mocked_slack_email.return_value.email = "test2@examle.com"

    # When
    result = process_confluence_oauth_callback(
        encrypted_state=mocked_user_with_sign_in_request.state,
        code="test_code",
    )

    # Then
    assert result == EmailMismatch()


class MyError(Exception):
    pass


def test_process_confluence_oauth_callback_fails_when_unable_to_get_confluence_email(
    mocked_user_with_sign_in_request: UserWithSignInRequest,
    mocked_confluence_email: MagicMock,
    mocked_slack_email: MagicMock,  # noqa: ARG001
) -> None:
    # Given
    mocked_confluence_email.side_effect = MyError()

    # When
    with pytest.raises(MyError) as exc_info:
        process_confluence_oauth_callback(
            encrypted_state=mocked_user_with_sign_in_request.state,
            code="test_code",
        )

    # Then
    assert exc_info


def test_process_confluence_oauth_callback_fails_when_unable_to_get_slack_email(
    mocked_user_with_sign_in_request: UserWithSignInRequest,
    mocked_confluence_email: MagicMock,  # noqa: ARG001
    mocked_slack_email: MagicMock,
) -> None:
    # Given
    mocked_slack_email.side_effect = MyError()

    # When
    with pytest.raises(MyError) as exc_info:
        process_confluence_oauth_callback(
            encrypted_state=mocked_user_with_sign_in_request.state,
            code="test_code",
        )

    # Then
    assert exc_info
