from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import BaseModel

from top_assist.auth._sign_in_context import SignInContext, register_sign_in_context_operation
from top_assist.auth.provider import UnauthenticatedUserError, authorize_for
from top_assist.confluence.oauth import ConfluenceOAuthTokens
from top_assist.confluence.policy import InvalidAuthError
from top_assist.models.user_auth import UserAuthDTO


@pytest.fixture()
def mocked_sign_in_context() -> Generator[SignInContext, None, None]:
    with patch("top_assist.auth.provider.sign_in_context_from_operation", autospec=True) as mock:
        value = Mock(SignInContext)
        mock.return_value = value
        yield value


@pytest.fixture()
def mocked_authenticated_user() -> Generator[UserAuthDTO, None, None]:
    with patch("top_assist.auth.provider.db_user_auth.find_by_slack_id", autospec=True) as mock:
        value = UserAuthDTO(
            id=-1,
            slack_user_id="authenticated_user_id",
            access_token="fake_encrypted_test_access_token",
            access_token_expires_at=datetime.now(UTC) + timedelta(seconds=3600),
            refresh_token="fake_encrypted_test_refresh_token",
            state=None,
            auth_message_id=None,
        )
        mock.return_value = value
        yield value


@pytest.fixture()
def mocked_authenticated_user_with_expired_token() -> Generator[UserAuthDTO, None, None]:
    with patch("top_assist.auth.provider.db_user_auth.find_by_slack_id", autospec=True) as mock:
        value = UserAuthDTO(
            id=-1,
            slack_user_id="authenticated_user_id",
            access_token="fake_encrypted_test_access_token",
            access_token_expires_at=datetime.now(UTC) - timedelta(seconds=3600),
            refresh_token="fake_encrypted_test_refresh_token",
            state=None,
            auth_message_id=None,
        )
        mock.return_value = value
        yield value


@pytest.fixture()
def mocked_unauthenticated_user() -> Generator[UserAuthDTO, None, None]:
    with patch("top_assist.auth.provider.db_user_auth.find_by_slack_id", autospec=True) as mock:
        value = UserAuthDTO(
            id=-1,
            slack_user_id="unauthenticated_user_id",
            access_token=None,
            access_token_expires_at=None,
            refresh_token=None,
            state=None,
            auth_message_id=None,
        )
        mock.return_value = value
        yield value


@pytest.fixture()
def mocked_tokens_with_refresh_token() -> Generator[MagicMock, None, None]:
    with patch("top_assist.auth.provider.tokens_with_refresh_token", autospec=True) as mock:
        mock.return_value = ConfluenceOAuthTokens(
            access_token="refreshed_test_access_token",
            refresh_token="refreshed_test_refresh_token",
            expires_in=3600,
        )
        yield mock


class MyOperation(BaseModel):
    something: str


def resume_my_operation(_operation: MyOperation) -> None:
    raise NotImplementedError


register_sign_in_context_operation(MyOperation, resume_my_operation)


def test_authorize_for_with_authorized_user(mocked_authenticated_user: UserAuthDTO) -> None:  # noqa: ARG001
    # Given
    test_operation = MyOperation(something="test_something")
    policy = None

    # When
    with authorize_for("authenticated_user_id", test_operation) as policy:
        pass

    # Then
    assert policy is not None
    assert policy.slack_user_id == "authenticated_user_id"
    assert policy.confluence_access_token == "test_access_token"


@patch("top_assist.auth.provider.db_user_auth.update_tokens", autospec=True)
def test_authorize_for_user_with_expired_token(
    mock_update_tokens: MagicMock,
    mocked_authenticated_user_with_expired_token: UserAuthDTO,  # noqa: ARG001
    mocked_tokens_with_refresh_token: MagicMock,  # noqa: ARG001
) -> None:
    # Given
    test_operation = MyOperation(something="test_something")
    policy = None

    # When
    with authorize_for("authenticated_user_id", test_operation) as policy:
        pass

    # Then
    assert policy is not None
    assert policy.slack_user_id == "authenticated_user_id"
    assert policy.confluence_access_token == "refreshed_test_access_token"
    mock_update_tokens.assert_called_once_with(
        slack_user_id="authenticated_user_id",
        access_token="fake_encrypted_refreshed_test_access_token",
        refresh_token="fake_encrypted_refreshed_test_refresh_token",
        expires_in=timedelta(seconds=3600),
    )


@patch("top_assist.auth.provider.start_sign_in_flow", autospec=True)
def test_authorize_for_user_with_expired_token_and_failed_refresh(
    mock_start_sign_in_flow: MagicMock,
    mocked_authenticated_user_with_expired_token: UserAuthDTO,  # noqa: ARG001
    mocked_tokens_with_refresh_token: MagicMock,
    mocked_sign_in_context: SignInContext,
) -> None:
    # Given
    mocked_tokens_with_refresh_token.side_effect = Exception("Failed to refresh tokens")
    test_operation = MyOperation(something="test_something")
    policy = None

    # When
    with pytest.raises(UnauthenticatedUserError), authorize_for("authenticated_user_id", test_operation) as policy:
        pass

    # Then
    assert policy is None
    mock_start_sign_in_flow.assert_called_once_with(mocked_sign_in_context)


@patch("top_assist.auth.provider.start_sign_in_flow", autospec=True)
def test_authorize_for_unathenticated_user(
    mock_start_sign_in_flow: MagicMock,
    mocked_unauthenticated_user: UserAuthDTO,  # noqa: ARG001
    mocked_sign_in_context: SignInContext,
) -> None:
    # Given
    test_operation = MyOperation(something="test_something")
    policy = None

    # When
    with pytest.raises(UnauthenticatedUserError), authorize_for("authenticated_user_id", test_operation) as policy:
        pass

    # Then
    assert policy is None
    mock_start_sign_in_flow.assert_called_once_with(mocked_sign_in_context)


@patch("top_assist.auth.provider.db_user_auth.delete_by_slack_id", autospec=True)
@patch("top_assist.auth.provider.start_sign_in_flow", autospec=True)
def test_authorize_for_with_authorized_user_having_invalid_token(
    mock_start_sign_in_flow: MagicMock,
    mock_delete_by_slack_id: MagicMock,
    mocked_authenticated_user: UserAuthDTO,  # noqa: ARG001
    mocked_sign_in_context: SignInContext,
) -> None:
    # Given
    test_operation = MyOperation(something="test_something")
    policy = None

    # When
    with pytest.raises(InvalidAuthError) as exc_info, authorize_for("authenticated_user_id", test_operation) as policy:
        raise InvalidAuthError("broken_user_id")

    # Then
    assert policy is not None
    assert policy.slack_user_id == "authenticated_user_id"
    assert policy.confluence_access_token == "test_access_token"
    assert exc_info.value.args == ("Invalid Auth for broken_user_id",)
    mock_delete_by_slack_id.assert_called_once_with("authenticated_user_id")
    mock_start_sign_in_flow.assert_called_once_with(mocked_sign_in_context)


class UnknownOperation(BaseModel):
    something: str


def test_authorize_for_with_unknown_operation() -> None:
    # Given
    operation = UnknownOperation(something="test_something")

    # When
    with pytest.raises(NotImplementedError) as exc_info, authorize_for("U123456", operation):
        pass

    # Then
    assert str(exc_info.value) == "Please register the operation class with register_sign_in_context_operation"
