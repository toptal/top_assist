import logging

from top_assist.slack.bot_runner import (
    SlackBotBlockActionTriggered,
    SlackBotEventMessage,
    SlackBotEventReactionAdded,
    SlackBotRouter,
    SlackBotTask,
)
from top_assist.slack.messages import is_feedback_action

from .tasks.question import QuestionEvent, process_question
from .tasks.user_feedback_score import process_user_feedback_score


class ChatBotRouter(SlackBotRouter):
    """Selects appropriate handlers for incoming events."""

    def __init__(self, *, known_question_thread_ids: list[str]) -> None:
        super().__init__()
        self.known_question_thread_ids: set[str] = set(known_question_thread_ids)

    def route_message(self, message: SlackBotEventMessage) -> SlackBotTask | None:
        log_extra = {
            "channel": message.channel,
            "item_ts": message.ts,
            "slack_user_id": message.user,
            "slack_thread_id": message.thread_ts,
        }

        logging.debug("Message received", extra=log_extra)

        if message.user == self.bot_user_id:
            logging.debug("Skipping message: message is from the bot itself", extra=log_extra)
            return None

        if "?" not in message.text and not message.is_direct_message():
            logging.debug("Skipping message: channel message without '?'", extra=log_extra)
            return None

        if message.thread_ts:
            logging.debug("Recognized the message as follow-up", extra=log_extra)
            if message.thread_ts not in self.known_question_thread_ids:
                logging.debug("Skipping message: reply to a message that is not a question", extra=log_extra)
                return None
        else:
            logging.debug("Recognized the message as question", extra=log_extra)
            self.known_question_thread_ids.add(message.ts)

        question = QuestionEvent(
            ts=message.ts,
            thread_ts=message.thread_ts,
            text=message.text,
            channel=message.channel,
            is_dm=message.is_direct_message(),
            user=message.user,
        )

        return SlackBotTask(process_question, question)

    def route_reaction(self, reaction: SlackBotEventReactionAdded) -> SlackBotTask | None:
        log_extra = {
            "item_ts": reaction.item.ts,
            "reaction": reaction.reaction,
            "slack_user_id": reaction.user,
        }

        logging.debug("Reaction received", extra=log_extra)
        # Map reactions to tasks here if needed
        #
        # if reaction.reaction == "+1":
        #     return None
        # else:
        logging.debug("Skipping reaction: irrelevant", extra=log_extra)
        return None

    def route_block_action(self, block_action: SlackBotBlockActionTriggered) -> SlackBotTask | None:
        if is_feedback_action(block_action):
            return SlackBotTask(process_user_feedback_score, block_action)
        else:
            logging.debug("Skipping block_action.", extra={"action_id": block_action.action_id})
            return None
