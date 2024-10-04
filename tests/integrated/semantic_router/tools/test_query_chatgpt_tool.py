from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage

from tests.integrated.semantic_router.factory import create_state
from top_assist.semantic_router.tools import query_chatgpt


@patch("top_assist.semantic_router.tools.query_chatgpt.query_chatgpt_with_openai", autospec=True)
def test_query_chatgpt(
    mock_query_chatgpt_with_openai: MagicMock,
) -> None:
    # Given
    state = create_state()
    expected_answer = "ChatGPT answer"
    mock_query_chatgpt_with_openai.return_value = MagicMock(
        message=expected_answer, assistant_thread_id="assistant_thread_id"
    )

    # When
    result = query_chatgpt.invoke(input={"state": state})

    # Then
    mock_query_chatgpt_with_openai.assert_called_once_with(
        question=state["prepared_question"], text_formatter=state["text_formatter"]
    )
    assert isinstance(result, AIMessage)
    assert result.content == expected_answer
    assert result.response_metadata == {"assistant_thread_id": "assistant_thread_id"}
