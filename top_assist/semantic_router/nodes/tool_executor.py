import logging

from langchain_core.tools import Tool

from top_assist.semantic_router.tools import tools
from top_assist.semantic_router.types import RouterState


class ToolNotFoundError(Exception):  # noqa: D101
    def __init__(self, tool_name: str) -> None:
        super().__init__(f"Router tried to call a tool that does not exist: {tool_name}")


class ToolNotCallableError(Exception):  # noqa: D101
    def __init__(self, tool_name: str) -> None:
        super().__init__(f"Router tried to call a tool that is not callable: {tool_name}.")


DEFAULT_TOOL = "query_knowledge_base"


def run_tool_executor(state: RouterState) -> dict:
    """Execute the tool that was chosen by the tool choice agent."""
    tool_call = state["tool_call"]

    if not tool_call:
        logging.warning("Tool calls not found in the state. Using the default tool.", extra={"state": state})
        tool_call_name = DEFAULT_TOOL
    else:
        tool_call_name = tool_call["name"]

    tool_to_use = __find_tool_by_name(tools, tool_call_name)

    if callable(tool_to_use.func):
        logging.info("Executing tool...", extra={"tool": tool_to_use.name})
        tool_response = tool_to_use.func(state)
    else:
        logging.error("Tool does not have a callable 'func' attribute.", extra={"tool": tool_to_use.name})
        raise ToolNotCallableError(tool_to_use.name)

    return {"messages": [tool_response]}


def __find_tool_by_name(tools: list, tool_name: str) -> Tool:
    for tool in tools:
        if tool.name == tool_name:
            return tool

    raise ToolNotFoundError(tool_name)
