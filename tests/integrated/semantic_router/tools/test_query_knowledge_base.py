from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage

from tests.integrated.semantic_router.factory import create_state
from top_assist.semantic_router.tools import query_knowledge_base


@patch("top_assist.semantic_router.tools.query_knowledge_base.query_confluence_knowledge_base", autospec=True)
def test_query_knowledge_base(
    mock_query_confluence_knowledge_base: MagicMock,
) -> None:
    # Given
    state = create_state(text_formatter=lambda text: text.upper())
    expected_answer = "Knowledge base answer"
    mock_query_confluence_knowledge_base.return_value = MagicMock(
        message=expected_answer, assistant_thread_id="assistant_thread_id"
    )

    # When
    result = query_knowledge_base.invoke(input={"state": state})

    # Then
    mock_query_confluence_knowledge_base.assert_called_once_with(
        question=state["prepared_question"],
        thread_id=state["assistant_thread_id"],
        access_policy=state["policy"],
        text_formatter=state["text_formatter"],
    )
    assert isinstance(result, AIMessage)
    assert result.content == expected_answer.upper()
    assert result.response_metadata == {"assistant_thread_id": "assistant_thread_id"}
