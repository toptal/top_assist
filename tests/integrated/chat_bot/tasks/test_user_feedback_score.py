from unittest.mock import MagicMock, patch

from tests.utils.factory import create_interaction_question
from top_assist.chat_bot.tasks.user_feedback_score import process_user_feedback_score
from top_assist.database.database import Session
from top_assist.models.user_feedback_score import UserFeedbackScoreORM
from top_assist.slack.bot_runner import SlackBotBlockActionTriggered


@patch("top_assist.chat_bot.tasks.user_feedback_score.mark_feedback_received", autospec=True)
def test_process_user_feedback_score(mock_mark_feedback_received: MagicMock, db_session: Session) -> None:
    block_action = SlackBotBlockActionTriggered(
        channel="fake_channel_id",
        ts="fake_ts",
        thread_ts="fake_thread_ts",
        action_id="user_feedback_score_like",
        user="fake_user_id",
        response_url="http://fake.url",
    )

    create_interaction_question(thread_id="fake_thread_ts", slack_user_id="fake_user_id")

    assert db_session.query(UserFeedbackScoreORM).count() == 0

    process_user_feedback_score(block_action)

    mock_mark_feedback_received.assert_called_once_with(thread_ts="fake_thread_ts", response_url="http://fake.url")

    user_feedback_score = (
        db_session.query(UserFeedbackScoreORM).filter(UserFeedbackScoreORM.slack_user_id == "fake_user_id").first()
    )

    assert user_feedback_score is not None

    assert user_feedback_score.positive
    assert user_feedback_score.channel_id == "fake_channel_id"
    assert user_feedback_score.thread_id == "fake_thread_ts"
    assert user_feedback_score.slack_user_id == "fake_user_id"
