import logging
from typing import Any

from slack_sdk.errors import SlackApiError

from top_assist.slack.bot_runner import SlackBotBlockActionTriggered
from top_assist.utils.tracer import ServiceNames, tracer

from ._client import PostedSlackMessage, WebClient

ACKNOWLEDGEMENT_REACTION = "eyes"


@tracer.wrap(service=ServiceNames.slack.value)
def post_answer_on_slack(
    answer: str,
    *,
    channel: str,
    thread_ts: str,
) -> PostedSlackMessage:
    result = WebClient.default().post_message(channel=channel, text=answer, thread_ts=thread_ts)

    return result


def post_channel_is_not_enabled(channel: str, thread_ts: str) -> None:
    WebClient.default().post_message(
        channel=channel, thread_ts=thread_ts, text="I'm not enabled for channels ATM, please ping me on DM"
    )


def delete_message(channel: str, ts: str) -> None:
    WebClient.default().delete_message(channel=channel, ts=ts)


FEEDBACK_ACTION_ID_PREFIX = "ta_user_feedback_score_"
FEEDBACK_TEXT = "Please review the Top Assist answers in this thread when you are done:"
FEEDBACK_BLOCKS: list[dict[Any, Any]] = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": FEEDBACK_TEXT,
        },
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": ":thumbsup:"},
                "action_id": f"{FEEDBACK_ACTION_ID_PREFIX}_like",
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": ":thumbsdown:"},
                "action_id": f"{FEEDBACK_ACTION_ID_PREFIX}_dislike",
            },
        ],
    },
]


@tracer.wrap(service=ServiceNames.slack.value)
def ask_for_feedback(*, channel: str, thread_ts: str, slack_user_id: str) -> None:
    WebClient.default().post_ephemeral(
        text=FEEDBACK_TEXT, channel=channel, thread_ts=thread_ts, blocks=FEEDBACK_BLOCKS, user=slack_user_id
    )


def is_feedback_action(action: SlackBotBlockActionTriggered) -> bool:
    return FEEDBACK_ACTION_ID_PREFIX in action.action_id


def is_feedback_action_positive(action: SlackBotBlockActionTriggered) -> bool:
    if action.action_id.endswith("_like"):
        return True
    if action.action_id.endswith("_dislike"):
        return False

    raise NotImplementedError(f"Unexpected action_id: {action.action_id}")


@tracer.wrap(service=ServiceNames.slack.value)
def mark_feedback_received(*, response_url: str, thread_ts: str) -> None:
    message = "Feedback registered, thanks!"

    WebClient.default().update_ephemeral(response_url=response_url, text=message, thread_ts=thread_ts)


@tracer.wrap(service=ServiceNames.slack.value)
def mark_message_as_acknowledged(channel: str, ts: str) -> None:
    try:
        WebClient.default().add_reaction(channel=channel, ts=ts, reaction=ACKNOWLEDGEMENT_REACTION)
        logging.info("Message acknowledged", extra={"channel": channel, "ts": ts})
    except SlackApiError as e:
        logging.exception(
            "Failed to acknowledge message", extra={"channel": channel, "ts": ts, "error": e.response["error"]}
        )


@tracer.wrap(service=ServiceNames.slack.value)
def send_confluence_auth_link(slack_user_id: str, link: str, message: str | None = None) -> PostedSlackMessage:
    web_client = WebClient.default()

    if not message:
        message = "To access the knowledge base, allow TopAssist to connect to your Confluence account"

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message,
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "style": "primary",
                    "text": {"type": "plain_text", "text": "Authorize Top Assist"},
                    "action_id": "confluence_auth_clicked",
                    "url": link,
                }
            ],
        },
    ]

    return web_client.post_message(
        channel=slack_user_id,
        text=message,
        blocks=blocks,
    )
