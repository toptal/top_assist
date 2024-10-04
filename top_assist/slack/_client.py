import logging
import typing

import backoff
from pydantic import BaseModel, EmailStr
from slack_sdk import WebClient as SDKWebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.webhook import WebhookClient as SDKWebhookClient

from top_assist.configuration import slack_bot_user_oauth_token
from top_assist.utils.service_cooldown import with_service_cooldown
from top_assist.utils.tracer import ServiceNames, tracer


class PostedSlackMessage(BaseModel):
    ts: str


class SlackThreadReply(BaseModel):
    ts: str
    user: str
    text: str


class ChannelInfo(BaseModel):
    id: str
    name: str
    is_member: bool


class UserInfoProfile(BaseModel):
    email: EmailStr


class UserInfoUser(BaseModel):
    is_email_confirmed: bool
    profile: UserInfoProfile


class WebClient:
    @classmethod
    def default(cls) -> typing.Self:
        return cls(token=slack_bot_user_oauth_token)

    def __init__(self, token: str):
        self.sdk_client = SDKWebClient(token=token)

    @tracer.wrap(service=ServiceNames.slack.value)
    def get_bot_user_id(self) -> str:
        response = self.sdk_client.auth_test()
        return response["user_id"]

    @tracer.wrap(service=ServiceNames.slack.value)
    def get_user_name_from_id(self, user_id: str, default: str) -> str:
        try:
            response = self.sdk_client.users_info(user=user_id)
            if response and response["user"]["name"]:
                return response["user"]["name"]
        except SlackApiError as e:
            logging.exception("Error fetching user name", extra={"user_id": user_id, "error": e.response["error"]})
        return default

    @tracer.wrap(service=ServiceNames.slack.value)
    @with_service_cooldown(
        service_key="slack_messaging",
        is_rate_limit_error=lambda e: isinstance(e, SlackApiError) and e.response["error"] == "ratelimited",
    )
    @backoff.on_exception(backoff.expo, TimeoutError, max_tries=2)
    def post_message(
        self,
        channel: str,
        thread_ts: str | None = None,
        text: str | None = None,
        blocks: list[dict] | None = None,
    ) -> PostedSlackMessage:
        response = self.sdk_client.chat_postMessage(channel=channel, text=text, thread_ts=thread_ts, blocks=blocks)

        return PostedSlackMessage(ts=response["ts"])

    @backoff.on_exception(backoff.expo, TimeoutError, max_tries=2)
    def post_ephemeral(  # noqa: PLR0913
        self, channel: str, thread_ts: str, user: str, text: str, blocks: list[dict] | None = None
    ) -> PostedSlackMessage:
        response = self.sdk_client.chat_postEphemeral(
            channel=channel, thread_ts=thread_ts, user=user, text=text, blocks=blocks
        )

        return PostedSlackMessage(ts=response["message_ts"])

    @tracer.wrap(service=ServiceNames.slack.value)
    def delete_message(self, channel: str, ts: str) -> None:
        try:
            self.sdk_client.chat_delete(channel=channel, ts=ts)
        except SlackApiError as e:
            logging.exception(
                "Failed to delete message",
                extra={"channel": channel, "ts": ts, "error": e.response["error"]},
            )
            raise

    @tracer.wrap(service=ServiceNames.slack.value)
    @with_service_cooldown(
        service_key="slack_messaging",
        is_rate_limit_error=lambda e: isinstance(e, SlackApiError) and e.response["error"] == "ratelimited",
    )
    @backoff.on_exception(backoff.expo, TimeoutError, max_tries=2)
    def update_message(
        self,
        channel: str,
        ts: str,
        text: str | None = None,
        blocks: list[dict] | None = None,
    ) -> PostedSlackMessage:
        response = self.sdk_client.chat_update(channel=channel, ts=ts, text=text, blocks=blocks)

        return PostedSlackMessage(ts=response["ts"])

    @tracer.wrap(service=ServiceNames.slack.value)
    @backoff.on_exception(backoff.expo, TimeoutError, max_tries=2)
    def update_ephemeral(self, response_url: str, text: str, thread_ts: str) -> None:
        webhook = SDKWebhookClient(response_url)
        response = webhook.send_dict(body={"replace_original": True, "text": text, "thread_ts": thread_ts})

        logging.info("Ephemeral message updated", extra={"response": response})

    @tracer.wrap(service=ServiceNames.slack.value)
    def conversations_replies(self, *, channel: str, ts: str) -> list[SlackThreadReply]:
        response = self.sdk_client.conversations_replies(channel=channel, ts=ts)
        parsed = _ResponseConversationsReplies(messages=response["messages"])
        return [
            SlackThreadReply(
                ts=reply.ts,
                user=reply.user,
                text=reply.text or "",
            )
            for reply in parsed.messages
        ]

    @tracer.wrap(service=ServiceNames.slack.value)
    def get_channel(self, channel_id: str) -> ChannelInfo | None:
        try:
            response = self.sdk_client.conversations_info(channel=channel_id)

            channel_data = response["channel"]

            # Ignore DMs
            if channel_data["is_im"]:
                return None

            return ChannelInfo(id=channel_data["id"], name=channel_data["name"], is_member=channel_data["is_member"])
        except SlackApiError as e:
            logging.error(  # noqa: TRY400
                "Error fetching channel, maybe it's a private channel and the bot was removed?",
                extra={"channel": channel_id, "error": e.response["error"]},
            )
            return None

    @tracer.wrap(service=ServiceNames.slack.value)
    def leave_channel(self, channel_id: str) -> bool:
        try:
            self.sdk_client.conversations_leave(channel=channel_id)

            return True
        except SlackApiError as e:
            logging.error("Failed to leave channel", extra={"channel": channel_id, "error": e.response["error"]})  # noqa: TRY400

            return False

    @tracer.wrap(service=ServiceNames.slack.value)
    def add_reaction(self, channel: str, ts: str, reaction: str) -> None:
        try:
            self.sdk_client.reactions_add(channel=channel, timestamp=ts, name=reaction)
        except SlackApiError as e:
            logging.exception(
                "Failed to add reaction",
                extra={"channel": channel, "ts": ts, "reaction": reaction, "error": e.response["error"]},
            )
            raise

    @tracer.wrap(service=ServiceNames.slack.value)
    def fetch_user_info(self, *, slack_user_id: str) -> UserInfoUser:
        try:
            response = self.sdk_client.users_info(user=slack_user_id)
            return _UserInfoResponse.model_validate(response.data).user

        except SlackApiError as e:
            logging.exception(
                "Failed to fetch user info",
                extra={"slack_user_id": slack_user_id, "error": e.response["error"]},
            )
            raise

        except Exception as e:
            logging.exception(
                "Failed to fetch user email",
                extra={"slack_user_id": slack_user_id, "error": str(e)},
            )
            raise


class _UserInfoResponse(BaseModel):
    user: UserInfoUser


class _ResponseConversationReply(BaseModel):
    ts: str
    user: str
    text: str | None


class _ResponseConversationsReplies(BaseModel):
    messages: list[_ResponseConversationReply]
