import logging

from top_assist.database import channels as db_channels
from top_assist.database import interactions as db_interactions
from top_assist.slack.channels import get_channel as slack_get_channel
from top_assist.slack.channels import leave_channel as slack_leave_channel


def update_channels() -> None:
    """Update/Load the channels based on previous interactions + considering if the bot is still a member of the channel."""
    slack_channel_ids = db_interactions.get_slack_channel_ids()
    for slack_channel_id in slack_channel_ids:
        slack_channel = slack_get_channel(slack_channel_id)

        if not slack_channel:
            logging.warning("Channel not found, removing/skipping", extra={"slack_channel_id": slack_channel_id})
            db_channels.delete_by_slack_channel_id(slack_channel_id)
            continue

        if not slack_channel.is_member:
            logging.info(
                "Bot is not a member of the channel, skipping",
                extra={"slack_channel_id": slack_channel_id, "channel_name": slack_channel.name},
            )
            db_channels.delete_by_slack_channel_id(slack_channel_id)
            continue

        logging.info(
            "Creating/Updating Channel", extra={"channel_id": slack_channel_id, "channel_name": slack_channel.name}
        )
        db_channels.upsert(slack_channel_id=slack_channel.id, name=slack_channel.name)


def leave_channel(channel_ids: list[int]) -> None:
    """Leave the channels and remove them from the database."""
    for channel_id in channel_ids:
        channel = db_channels.find_by_id(channel_id)

        if channel and slack_leave_channel(channel.slack_channel_id):
            logging.info(
                "Bot left channel",
                extra={
                    "channel_id": channel_id,
                    "slack_channel_id": channel.slack_channel_id,
                    "channel_name": channel.name,
                },
            )
            db_channels.delete_by_id(channel_id)
