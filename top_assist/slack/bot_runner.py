import abc
import logging
import time
from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor
from typing import TypeVar

from pydantic import BaseModel
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from top_assist.configuration import (
    slack_allow_enterprise_id,
    slack_allow_team_id,
    slack_app_level_token,
    slack_listener_workers_num,
)
from top_assist.utils.metrics import start_metrics_server
from top_assist.utils.sentry_notifier import sentry_notify_exception, sentry_notify_issue
from top_assist.utils.tracer import ServiceNames, tracer

from ._client import WebClient

_T = TypeVar("_T")  # mypy: PEP 695 generics are not yet supported


class SlackBotEventMessage(BaseModel):
    """Represents a message event sent by a user in Slack.

    Attr:
        channel: str - the channel ID where the message was sent
        text: str - the text of the message
        thread_ts: str | None - the timestamp of the thread where the message was sent. None if it's not a thread
        ts: str - the timestamp of the message
        user: str - the ID of the user who sent the message
        channel_type: str - the type of the channel where the message was sent. Can be "im" for direct messages
    """

    channel: str
    text: str
    thread_ts: str | None = None
    ts: str
    user: str
    channel_type: str

    def is_direct_message(self) -> bool:
        return self.channel_type == "im"


class SlackBotEventReactionSubject(BaseModel):  # noqa: D101
    channel: str
    ts: str
    type: str


class SlackBotEventReactionAdded(BaseModel):  # noqa: D101
    event_ts: str
    item: SlackBotEventReactionSubject
    reaction: str
    user: str


class SlackBotBlockActionTriggered(BaseModel):
    """Represents a block action triggered by a user in Slack.

    Attr:
        channel: str - the channel ID where the action was triggered
        ts: str - the timestamp of the message where the action was triggered
        thread_ts: str | None - the timestamp of the thread where the action was triggered
        action_id: str - the ID of the action
        user: str - the ID of the user who triggered the action
        response_url: str - the URL to send the response to
    """

    channel: str
    ts: str
    thread_ts: str | None
    action_id: str
    user: str
    response_url: str


class SlackBotTask:
    """Represents a task to be executed by the bot."""

    def __init__(self, handler: Callable[[_T], None], event: _T):
        """Initialize the task with the handler and the event to be processed.

        Args:
            handler: Callable[[_T], None] - the handler to process the event
            event: _T - the event to be processed
        """
        self.handler = handler
        self.event = event


class SlackBotRouter(abc.ABC):
    """Routes Slack events to the appropriate handler."""

    def __init__(self):
        """Initialize the router with the bot user ID."""
        self.bot_user_id = WebClient.default().get_bot_user_id()

    @abc.abstractmethod
    def route_message(self, message: SlackBotEventMessage) -> SlackBotTask | None:
        raise NotImplementedError

    @abc.abstractmethod
    def route_reaction(self, reaction: SlackBotEventReactionAdded) -> SlackBotTask | None:
        raise NotImplementedError

    @abc.abstractmethod
    def route_block_action(self, block_action: SlackBotBlockActionTriggered) -> SlackBotTask | None:
        raise NotImplementedError


def run_bot(router: SlackBotRouter, trace_service: ServiceNames) -> None:
    socket_mode_client = SocketModeClient(app_token=slack_app_level_token)
    # force disable HTTP proxy as it does not work well with websocket traffic
    socket_mode_client.proxy = None

    start_metrics_server(multiprocess=True)

    with ProcessPoolExecutor(max_workers=slack_listener_workers_num) as executor:
        dispatcher = _Dispatcher(executor, router, trace_service)
        socket_mode_client.socket_mode_request_listeners.append(dispatcher)  # type: ignore[arg-type]

        try:
            socket_mode_client.connect()
        except Exception as e:
            logging.critical("Error connecting to the slack RTM API", exc_info=True, stack_info=True)
            sentry_notify_exception(e, tags={"module": "bot"})
            raise

        logging.info("Bot connected...")
        try:
            while True:
                logging.debug("Bot is running...")
                time.sleep(10)
        except KeyboardInterrupt:
            logging.debug("Bot stopped by the user")
            executor.shutdown(wait=True)
        except Exception as e:
            logging.critical("Bot stopped due to an exception", exc_info=True, stack_info=True)
            sentry_notify_exception(e, tags={"module": "bot"})
            executor.shutdown(wait=True)


class _Dispatcher:
    def __init__(self, executor: ProcessPoolExecutor, router: SlackBotRouter, trace_service: ServiceNames):
        self.executor = executor
        self.router = router
        self.trace_service = trace_service

    def __call__(self, client: SocketModeClient, req: SocketModeRequest) -> None:
        with tracer.trace(name="socket_mode_request_listener", service=self.trace_service.value):
            try:
                # Acknowledge the event immediately
                client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))

                self.__process_event(req)

            except Exception as e:
                logging.exception("Error processing payload", extra={"payload": self.__filtered_payload(req.payload)})
                sentry_notify_exception(e, tags={"module": "bot"})
                return

    def __process_event(self, req: SocketModeRequest) -> None:
        # Uncomment when recording websocket comms
        # logging.info("Incoming request: ", extra=vars(req))
        if req.payload.get("type") == "block_actions":
            enterprise_id = req.payload.get("enterprise", {}).get("id", None)
            team_id = req.payload.get("team", {}).get("id", None)
        elif req.payload.get("type") == "event_callback":
            enterprise_id = req.payload.get("enterprise_id", None)
            team_id = req.payload.get("team_id", None)
        else:
            logging.warning("Skipping unknown payload type", extra={"payload": self.__filtered_payload(req.payload)})
            return

        if not self.__is_authorized(enterprise_id, team_id):
            logging.warning(
                "Skipping unauthorized event",
                extra={"enterprise_id": enterprise_id, "team_id": team_id},
            )
            return

        task = self.__route(req)
        if task is None:
            return

        self.__submit_task(task.handler, task.event)

    def __is_authorized(self, enterprise_id: str, team_id: str) -> bool:
        """Authorize the request based on the enterprise_id and team_id."""
        if slack_allow_enterprise_id not in ("*", enterprise_id):
            return False

        if slack_allow_team_id not in ("*", team_id):
            return False

        return True

    def __route(self, req: SocketModeRequest) -> SlackBotTask | None:
        payload = req.payload
        event = payload.get("event", {})

        if bool(event):
            return self.__route_events(event)

        if payload.get("type") == "block_actions":
            return self.__route_block_actions(payload)

        logging.info("Unhandled Slack payload:", extra={"payload": self.__filtered_payload(payload)})
        return None

    def __route_events(self, event: dict) -> SlackBotTask | None:
        if event.get("type") == "message" and "subtype" not in event:
            message = SlackBotEventMessage(**event)
            return self.router.route_message(message)
        elif event.get("type") == "reaction_added":
            reaction = SlackBotEventReactionAdded(**event)
            return self.router.route_reaction(reaction)
        else:
            logging.info(
                "Skipping event: irrelevant event", extra={"type": event.get("type"), "subtype": event.get("subtype")}
            )
            return None

    def __route_block_actions(self, payload: dict) -> SlackBotTask | None:
        action_list = payload.get("actions", [])
        if len(action_list) > 1:
            sentry_notify_issue(
                "Block action event with multiple actions", extra={"payload": self.__filtered_payload(payload)}
            )
            # proceed with the first action

        action = action_list[0]

        block_action = SlackBotBlockActionTriggered(
            channel=payload.get("channel", {}).get("id"),
            ts=payload.get("message", {}).get("ts") or payload.get("container", {}).get("message_ts"),
            thread_ts=payload.get("message", {}).get("thread_ts") or payload.get("container", {}).get("thread_ts"),
            action_id=action.get("action_id"),
            user=payload.get("user", {}).get("id"),
            response_url=payload["response_url"],
        )

        return self.router.route_block_action(block_action)

    def __submit_task(self, handler: Callable[[_T], None], event: _T) -> None:
        def completion_callback(future: Future[None]) -> None:
            try:
                future.result()
            except Exception as e:
                logging.exception("Error processing task", extra={"event": event})
                sentry_notify_exception(e, tags={"module": "bot.worker"})

        future = self.executor.submit(handler, event)
        future.add_done_callback(completion_callback)

    def __filtered_payload(self, payload: dict) -> dict:
        exclude_keys = ("token", "authed_users")
        return {k: v for k, v in payload.items() if k not in exclude_keys}
