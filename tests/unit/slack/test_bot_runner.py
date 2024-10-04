from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from top_assist.chat_bot.router import ChatBotRouter
from top_assist.chat_bot.tasks.question import QuestionEvent, process_question
from top_assist.chat_bot.tasks.user_feedback_score import process_user_feedback_score
from top_assist.slack.bot_runner import (
    SlackBotBlockActionTriggered,
    _Dispatcher,
)
from top_assist.utils.tracer import ServiceNames


@pytest.fixture(autouse=True)
def _patch_slack_web_client() -> Generator:
    with patch("top_assist.slack.bot_runner.WebClient") as mock_web_client_class:
        mock_web_client = MagicMock()
        mock_web_client_class.default = mock_web_client
        yield


@patch("top_assist.slack.bot_runner.SocketModeClient")
@patch("top_assist.slack.bot_runner.SocketModeResponse")
def test_dispatcher_with_block_action(mock_socket_client: MagicMock, mock_socket_mode_response: MagicMock) -> None:
    mock_executor = MagicMock()

    dispatcher = _Dispatcher(
        executor=mock_executor, router=ChatBotRouter(known_question_thread_ids=[]), trace_service=ServiceNames.chat_bot
    )

    mock_socket_mode_response.payload = {
        "type": "block_actions",
        "channel": {"id": "fake_channel_id"},
        "message": {"ts": "fake_ts", "thread_ts": "fake_thread_ts"},
        "user": {"id": "fake_user_id"},
        "response_url": "http://fake.url",
        "actions": [
            {
                "action_id": "ta_user_feedback_score_like",
                "value": "1",
            }
        ],
    }

    dispatcher(mock_socket_client, mock_socket_mode_response)

    expected_event = SlackBotBlockActionTriggered(
        channel="fake_channel_id",
        ts="fake_ts",
        thread_ts="fake_thread_ts",
        action_id="ta_user_feedback_score_like",
        user="fake_user_id",
        response_url="http://fake.url",
    )

    assert mock_socket_client.send_socket_mode_response.called

    mock_executor.submit.assert_called_with(process_user_feedback_score, expected_event)


@patch("top_assist.slack.bot_runner.SocketModeClient")
@patch("top_assist.slack.bot_runner.SocketModeResponse")
def test_dispatcher_with_a_root_question(mock_socket_client: MagicMock, mock_socket_mode_response: MagicMock) -> None:
    mock_executor = MagicMock()

    dispatcher = _Dispatcher(
        executor=mock_executor, router=ChatBotRouter(known_question_thread_ids=[]), trace_service=ServiceNames.chat_bot
    )

    mock_socket_mode_response.payload = {
        "type": "event_callback",
        "event": {
            "type": "message",
            "channel": "fake_channel_id",
            "channel_type": "public",
            "ts": "1720529274.015000",
            "user": "fake_user_id",
            "text": "Is this a fake question?",
        },
    }

    dispatcher(mock_socket_client, mock_socket_mode_response)

    expected_event = QuestionEvent(
        channel="fake_channel_id",
        ts="1720529274.015000",
        thread_ts=None,
        text="Is this a fake question?",
        user="fake_user_id",
        is_dm=False,
    )

    assert mock_socket_client.send_socket_mode_response.called

    mock_executor.submit.assert_called_with(process_question, expected_event)


@patch("top_assist.slack.bot_runner.SocketModeClient")
@patch("top_assist.slack.bot_runner.SocketModeResponse")
def test_dispatcher_with_a_root_question_to_gpt(
    mock_socket_client: MagicMock,
    mock_socket_mode_response: MagicMock,
) -> None:
    mock_executor = MagicMock()

    dispatcher = _Dispatcher(
        executor=mock_executor, router=ChatBotRouter(known_question_thread_ids=[]), trace_service=ServiceNames.chat_bot
    )

    mock_socket_mode_response.payload = {
        "type": "event_callback",
        "event": {
            "type": "message",
            "channel": "fake_channel_id",
            "channel_type": "public",
            "ts": "1720529274.015000",
            "user": "fake_user_id",
            "text": "-chat Is this a fake question to GPT?",
        },
    }

    dispatcher(mock_socket_client, mock_socket_mode_response)

    expected_event = QuestionEvent(
        channel="fake_channel_id",
        ts="1720529274.015000",
        thread_ts=None,
        text="-chat Is this a fake question to GPT?",
        user="fake_user_id",
        is_dm=False,
    )

    assert mock_socket_client.send_socket_mode_response.called

    mock_executor.submit.assert_called_with(process_question, expected_event)
