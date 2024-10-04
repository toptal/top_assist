from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage

from top_assist.semantic_router.router import FALLBACK_MSG, __format_as_slack_markup, route
from top_assist.semantic_router.types import HistoryEntry, SemanticRouterResponse


@patch("top_assist.semantic_router.router.main_graph", autospec=True)
def test_router(
    mock_main_graph: MagicMock,
) -> None:
    # Given
    expected_answer = "The answer is 42"
    expected_assistant_thread_id = "thread_AAA000"
    history: list[HistoryEntry] = []
    policy = MagicMock()

    mock_main_graph.invoke.return_value = {
        "history": history,
        "prepared_question": "I am a prepared question",
        "policy": policy,
        "assistant_thread_id": "some_thread_id_123",
        "messages": [
            AIMessage(content="The answer from some tool"),
            AIMessage(content=expected_answer, response_metadata={"assistant_thread_id": expected_assistant_thread_id}),
        ],
    }

    # When
    result = route(history, policy, None)

    # Then
    mock_main_graph.invoke.assert_called_once()
    assert isinstance(result, SemanticRouterResponse)
    assert result.message == expected_answer
    assert result.assistant_thread_id == expected_assistant_thread_id


@patch("top_assist.semantic_router.router.main_graph", autospec=True)
def test_router_with_error(
    mock_main_graph: MagicMock,
) -> None:
    # Given
    history: list[HistoryEntry] = []
    policy = MagicMock()

    mock_main_graph.invoke.side_effect = Exception("Some error")

    # When
    result = route(history, policy, None)

    # Then
    assert isinstance(result, SemanticRouterResponse)
    assert result.message == FALLBACK_MSG
    assert result.assistant_thread_id is None


def test__format_as_slack_markup() -> None:
    # Given
    text = """
    **This is bold text**
    [this is a link](https://www.example.com) that should be converted to a Slack link
    """
    expected_text = """
    *This is bold text*
    <https://www.example.com|this is a link> that should be converted to a Slack link
    """

    # When
    result = __format_as_slack_markup(text)

    # Then
    assert result == expected_text
