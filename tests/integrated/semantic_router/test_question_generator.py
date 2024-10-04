from unittest.mock import MagicMock, patch

from tests.integrated.semantic_router.factory import create_state
from top_assist.semantic_router.nodes.question_generator import run_question_generator
from top_assist.semantic_router.types import HistoryEntry


@patch("top_assist.semantic_router.nodes.question_generator.llm", autospec=True)
def test_run_question_generator(mock_llm: MagicMock) -> None:
    # Given
    expected_prepared_question = "Very interesting question."
    state = create_state(history=[HistoryEntry(role="user", content=expected_prepared_question)])

    # When
    res = run_question_generator(state=state)

    # Then
    assert not mock_llm.called
    assert res == {"prepared_question": expected_prepared_question}


@patch("top_assist.semantic_router.nodes.question_generator.llm", autospec=True)
def test_run_question_generator_with_history(mock_llm: MagicMock) -> None:
    # Given
    state = create_state(
        history=[
            HistoryEntry(role="user", content="Init question."),
            HistoryEntry(role="assistant", content="Some history event"),
        ]
    )
    expected_prepared_question = "Very interesting question."

    mock_llm.with_structured_output.return_value = mock_llm
    mock_llm.invoke.return_value = MagicMock(prepared_question=expected_prepared_question)

    # When
    res = run_question_generator(state=state)

    # Then
    mock_llm.invoke.assert_called_once()
    assert res == {"prepared_question": expected_prepared_question}
