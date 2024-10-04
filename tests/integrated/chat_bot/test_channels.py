from unittest.mock import MagicMock, patch

from tests.utils import factory, matchers
from top_assist.chat_bot import channels
from top_assist.database.database import Session
from top_assist.models.channel import ChannelORM
from top_assist.slack._client import ChannelInfo, WebClient


@patch("top_assist.slack._client.WebClient.get_channel", autospec=True)
def test_update_channels(mock_slack_get_channel: MagicMock, db_session: Session) -> None:
    interaction = factory.create_interaction_question()

    mock_slack_get_channel.return_value = ChannelInfo(
        id=interaction.channel_id,
        name="fake_channel_name",
        is_member=True,
    )

    channels.update_channels()

    mock_slack_get_channel.assert_called_once_with(matchers.IsInstanceOf(WebClient), interaction.channel_id)

    assert db_session.query(ChannelORM).count() == 1

    added_channel = db_session.query(ChannelORM).first()

    assert added_channel
    assert added_channel.slack_channel_id == interaction.channel_id
    assert added_channel.name == "fake_channel_name"


@patch("top_assist.slack._client.WebClient.get_channel", autospec=True)
def test_update_channels_failed(mock_slack_get_channel: MagicMock, db_session: Session) -> None:
    interaction = factory.create_interaction_question()
    factory.create_channel(slack_channel_id=interaction.channel_id)

    mock_slack_get_channel.return_value = None

    assert db_session.query(ChannelORM).count() == 1

    channels.update_channels()

    mock_slack_get_channel.assert_called_once_with(matchers.IsInstanceOf(WebClient), interaction.channel_id)

    assert db_session.query(ChannelORM).count() == 0, "Channel should be removed from the database"


@patch("top_assist.slack._client.WebClient.get_channel", autospec=True)
def test_update_channels_not_a_member(mock_slack_get_channel: MagicMock, db_session: Session) -> None:
    interaction = factory.create_interaction_question()
    factory.create_channel(slack_channel_id=interaction.channel_id)

    mock_slack_get_channel.return_value = ChannelInfo(
        id=interaction.channel_id, name="fake_channel_name", is_member=False
    )

    assert db_session.query(ChannelORM).count() == 1

    channels.update_channels()

    mock_slack_get_channel.assert_called_once_with(matchers.IsInstanceOf(WebClient), interaction.channel_id)

    assert db_session.query(ChannelORM).count() == 0, "Channel should be removed from the database"


@patch("top_assist.slack._client.WebClient.leave_channel", autospec=True)
def test_leave_channel(mock_slack_leave_channel: MagicMock, db_session: Session) -> None:
    channel = factory.create_channel()

    mock_slack_leave_channel.return_value = True

    assert db_session.query(ChannelORM).count() == 1

    channels.leave_channel([channel.id])

    mock_slack_leave_channel.assert_called_once_with(matchers.IsInstanceOf(WebClient), channel.slack_channel_id)

    assert db_session.query(ChannelORM).count() == 0


@patch("top_assist.slack._client.WebClient.leave_channel", autospec=True)
def test_leave_channel_failed(mock_slack_leave_channel: MagicMock, db_session: Session) -> None:
    channel = factory.create_channel()

    mock_slack_leave_channel.return_value = False

    assert db_session.query(ChannelORM).count() == 1

    channels.leave_channel([channel.id])

    mock_slack_leave_channel.assert_called_once_with(matchers.IsInstanceOf(WebClient), channel.slack_channel_id)

    assert db_session.query(ChannelORM).count() == 1
