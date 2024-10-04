from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, TypedDict

from langgraph.graph import MessagesState

from top_assist.confluence.policy import PageAccessPolicy


class HistoryEntry(TypedDict):
    """Represents a message in the history of the current Slack thread."""

    role: Literal["user", "assistant", "system"]
    content: str


class RouterState(MessagesState):
    """Represents the state of the semantic router graph.

    Attr:
        prepared_question: str | None - The AI prepared question based on the user input
        tool_call: dict | None - The tool call to be made
        history: list[HistoryEntry] - The history of the current Slack thread
        policy: PageAccessPolicy | None - The access policy to Confluence pages
        assistant_thread_id: str | None - The thread ID of the AI assistant if it is created during current thread
        text_formatter: Callable[[str], str] - The text formatter for preparing the final response message
    """

    prepared_question: str | None
    tool_call: dict | None
    history: list[HistoryEntry]
    policy: PageAccessPolicy | None
    assistant_thread_id: str | None
    text_formatter: Callable[[str], str]


@dataclass
class SemanticRouterResponse:
    """Represents the response of the semantic router.

    Attr:
        message: str - The message to be displayed to the user
        assistant_thread_id: str -  The thread ID of the AI assistant if it is created
    """

    message: str
    assistant_thread_id: str | None
