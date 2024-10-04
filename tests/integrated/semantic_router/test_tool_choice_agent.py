from unittest.mock import MagicMock, patch

from tests.integrated.semantic_router.factory import create_state
from top_assist.semantic_router.nodes.tool_choice_agent import run_tool_choice_agent
from top_assist.semantic_router.types import HistoryEntry


@patch("top_assist.semantic_router.nodes.tool_choice_agent.llm", autospec=True)
def test_run_tool_choice_agent(mock_llm: MagicMock) -> None:
    # Given
    state = create_state(
        history=[HistoryEntry(role="user", content="Some init question.")], prepared_question="Some prepared question."
    )
    chosen_tool = MagicMock()
    llm_response = MagicMock(tool_calls=[chosen_tool])

    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = llm_response

    # When
    res = run_tool_choice_agent(state=state)

    # Then
    assert mock_llm.bind_tools.called
    assert mock_llm.invoke.called
    assert res == {"messages": [llm_response], "tool_call": chosen_tool}


@patch("top_assist.semantic_router.nodes.tool_choice_agent.llm", autospec=True)
def test_run_tool_choice_agent_return_none(mock_llm: MagicMock) -> None:
    # Given
    state = create_state(
        history=[HistoryEntry(role="user", content="Some init question.")], prepared_question="Some prepared question."
    )

    llm_response = "Some response"  # LLM returns no tool call

    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = llm_response

    # When
    res = run_tool_choice_agent(state=state)

    # Then
    assert mock_llm.bind_tools.called
    assert mock_llm.invoke.called
    assert res == {"messages": [llm_response], "tool_call": None}
