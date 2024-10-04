from collections.abc import Generator
from unittest.mock import patch

import pytest
from langchain_core.tools import tool

from tests.integrated.semantic_router.factory import create_state
from top_assist.semantic_router.nodes.tool_executor import ToolNotCallableError, ToolNotFoundError, run_tool_executor


@tool
def mock_query_chatgpt(state: dict) -> dict:
    """Mock function for query_chatgpt"""
    return {"content": f"Mock response from query_chatgpt {state}"}


@tool
def mock_web_search(state: dict) -> dict:
    """Mock function for web_search"""
    return {"content": f"Mock response from web_search {state}"}


@pytest.fixture()
def mock_tools_list() -> Generator:
    with patch(
        "top_assist.semantic_router.nodes.tool_executor.tools",
        new_callable=lambda: [mock_query_chatgpt, mock_web_search],
    ):
        yield [mock_query_chatgpt, mock_web_search]


class NonCallableTool:
    def __init__(self):
        self.name = "not_a_tool"
        self.func = "this is not callable"


@pytest.mark.usefixtures("mock_tools_list")
def test_run_tool_executor() -> None:
    # Given
    tool_call = {"name": "mock_query_chatgpt", "args": {}, "id": "call_123", "type": "tool_call"}
    state = create_state(tool_call=tool_call)

    # When
    res = run_tool_executor(state=state)

    # Then
    assert res == {"messages": [{"content": f"Mock response from query_chatgpt {state}"}]}


@pytest.mark.usefixtures("mock_tools_list")
def test_run_tool_executor_when_wrong_name() -> None:
    # Given
    tool_call = {"name": "mock_WRONG_NAME", "args": {}, "id": "call_123", "type": "tool_call"}
    state = create_state(tool_call=tool_call)

    # When
    with pytest.raises(ToolNotFoundError) as exc_info:
        run_tool_executor(state=state)

    # Then
    assert str(exc_info.value) == "Router tried to call a tool that does not exist: mock_WRONG_NAME"


@pytest.mark.usefixtures("mock_tools_list")
@patch("top_assist.semantic_router.nodes.tool_executor.DEFAULT_TOOL", new_callable=lambda: "mock_web_search")
def test_run_tool_executor_when_no_tool_chosen(default_tool: str) -> None:  # noqa: ARG001
    # Given
    tool_call = None
    state = create_state(tool_call=tool_call)

    # When
    res = run_tool_executor(state=state)

    # Then
    assert res == {"messages": [{"content": f"Mock response from web_search {state}"}]}


@patch("top_assist.semantic_router.nodes.tool_executor.tools", new_callable=lambda: [NonCallableTool()])
def test_run_tool_executor_when_tool_is_not_func(mock_tools_list: list) -> None:  # noqa: ARG001
    # Given
    tool_call = {"name": "not_a_tool", "args": {}, "id": "call_123", "type": "tool_call"}

    # When
    with pytest.raises(ToolNotCallableError) as exc_info:
        run_tool_executor(state=create_state(tool_call=tool_call))

    # Then
    assert str(exc_info.value) == "Router tried to call a tool that is not callable: not_a_tool."
