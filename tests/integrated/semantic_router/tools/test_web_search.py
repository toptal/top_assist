from unittest.mock import MagicMock, patch

from langchain.agents import AgentExecutor
from langchain.agents.agent import RunnableMultiActionAgent
from langchain_core.messages import AIMessage

from tests.integrated.semantic_router.factory import create_state
from top_assist.semantic_router.tools.web_search import (
    FALLBACK_MSG,
    __create_agent,
    llm,
    prompt_template,
    web_search,
    web_search_tools,
)


@patch("top_assist.semantic_router.tools.web_search.__create_agent", autospec=True)
def test_web_search(
    mock_create_agent: MagicMock,
) -> None:
    # Given
    state = create_state()
    expected_output = "The answer is 42"
    mock_agent_executor = MagicMock()
    mock_agent_executor.invoke.return_value = {"output": expected_output}
    mock_create_agent.return_value = mock_agent_executor

    # When
    result = web_search.invoke(input={"state": state})

    # Then
    mock_create_agent.assert_called_once()
    mock_agent_executor.invoke.assert_called_once_with({"input": state["prepared_question"]})
    assert isinstance(result, AIMessage)
    assert result.content == expected_output


@patch("top_assist.semantic_router.tools.web_search.__create_agent", autospec=True)
def test_web_search_with_error(mock_create_agent: MagicMock) -> None:
    # Given
    state = create_state()
    mock_create_agent.side_effect = Exception("Some error")

    # When
    result = web_search.invoke(input={"state": state})

    # Then
    assert isinstance(result, AIMessage)
    assert result.content == FALLBACK_MSG


def test_create_agent() -> None:
    # When
    result = __create_agent(llm, web_search_tools, prompt_template)

    # Then
    assert isinstance(result, AgentExecutor)
    assert isinstance(result.agent, RunnableMultiActionAgent)
