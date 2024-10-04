from unittest.mock import MagicMock, Mock, patch

from top_assist.auth.sign_in_flow import (
    SignInContext,
    start_sign_in_flow,
)
from top_assist.database.user_auth import RequestUpsertResult
from top_assist.slack._client import PostedSlackMessage


@patch("top_assist.auth.sign_in_flow.send_confluence_auth_link", autospec=True)
@patch("top_assist.auth.sign_in_flow.delete_message", autospec=True)
@patch("top_assist.auth.sign_in_flow.db_user_auth.upsert_request", autospec=True)
def test_start_sign_in_flow_from_scratch(
    mock_upsert_request: MagicMock,
    mock_delete_message: MagicMock,
    mock_send_confluence_auth_link: MagicMock,
) -> None:
    # Given
    mock_send_confluence_auth_link.return_value = Mock(PostedSlackMessage, ts="test_ts")
    mock_upsert_request.return_value = Mock(RequestUpsertResult, old_auth_message_id=None)

    # When
    start_sign_in_flow(SignInContext(slack_user_id="U123456", encrypted_state="fake_encrypted_state"))

    # Then
    mock_send_confluence_auth_link.assert_called_once_with(
        "U123456",
        "http://localhost:8080/confluence/oauth/redirect/fake_encrypted_state",
    )
    mock_upsert_request.assert_called_once_with(
        slack_user_id="U123456",
        encrypted_state="fake_encrypted_state",
        auth_message_id="test_ts",
    )
    mock_delete_message.assert_not_called()


@patch("top_assist.auth.sign_in_flow.send_confluence_auth_link", autospec=True)
@patch("top_assist.auth.sign_in_flow.delete_message", autospec=True)
@patch("top_assist.auth.sign_in_flow.db_user_auth.upsert_request", autospec=True)
def test_start_sign_in_flow_again(
    mock_upsert_request: MagicMock,
    mock_delete_message: MagicMock,
    mock_send_confluence_auth_link: MagicMock,
) -> None:
    # Given
    mock_send_confluence_auth_link.return_value = Mock(PostedSlackMessage, ts="test_ts")
    mock_upsert_request.return_value = Mock(RequestUpsertResult, old_auth_message_id="old_auth_message_id")

    # When
    start_sign_in_flow(SignInContext(slack_user_id="U123456", encrypted_state="fake_encrypted_state"))

    # Then
    mock_send_confluence_auth_link.assert_called_once_with(
        "U123456",
        "http://localhost:8080/confluence/oauth/redirect/fake_encrypted_state",
    )
    mock_upsert_request.assert_called_once_with(
        slack_user_id="U123456",
        encrypted_state="fake_encrypted_state",
        auth_message_id="test_ts",
    )
    mock_delete_message.assert_called_once_with(channel="U123456", ts="old_auth_message_id")
