from collections.abc import Callable

from top_assist.confluence.policy import PageAccessPolicy
from top_assist.semantic_router.types import RouterState


def create_state(
    history: list | None = None,
    messages: list | None = None,
    prepared_question: str = "Some question",
    tool_call: dict | None = None,
    policy: PageAccessPolicy | None = None,
    assistant_thread_id: str | None = None,
    text_formatter: Callable = lambda x: x,
) -> RouterState:
    return RouterState(
        prepared_question=prepared_question,
        tool_call=tool_call,
        history=history or [],
        policy=policy,
        assistant_thread_id=assistant_thread_id,
        text_formatter=text_formatter,
        messages=messages or [],
    )
