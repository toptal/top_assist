from unittest.mock import MagicMock, patch

from top_assist.open_ai.assistants.threads import ThreadCompletion
from top_assist.open_ai.query import query_chatgpt


@patch("top_assist.open_ai.query.add_user_message_and_complete", autospec=True)
def test_query_chatgpt(mock_add_user_message_and_complete: MagicMock) -> None:
    # Given
    question = "That is my question"
    ai_response = "That is the  AI response"
    expected_thread_id = "1234567890"
    mock_add_user_message_and_complete.return_value = ThreadCompletion(
        message=ai_response, thread_id=expected_thread_id
    )

    # When
    res = query_chatgpt(question=question)

    # Then
    assert res.message == ai_response
    assert res.assistant_thread_id == expected_thread_id


@patch("top_assist.open_ai.query.add_user_message_and_complete", autospec=True)
def test_query_chatgpt_with_text_formatter(mock_add_user_message_and_complete: MagicMock) -> None:
    # Given
    question = "That is my question"
    ai_response = "That is the  AI response"
    expected_thread_id = "1234567890"
    mock_add_user_message_and_complete.return_value = ThreadCompletion(
        message=ai_response, thread_id=expected_thread_id
    )

    # When
    res = query_chatgpt(question=question, text_formatter=lambda x: x.upper())

    # Then
    assert res.message == ai_response.upper()
    assert res.assistant_thread_id == expected_thread_id
