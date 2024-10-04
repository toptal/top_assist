from typing import cast
from unittest.mock import MagicMock, patch

import pook
import pytest
from langchain_core.messages import AIMessage

from tests.integrated.semantic_router.factory import create_state
from top_assist.semantic_router.tools.prompt_optimizer import (
    FALLBACK_MSG,
    DifyResponseError,
    PreparedTask,
    query_prompt_optimizer,
    run_on_dify,
)


@patch("top_assist.semantic_router.tools.prompt_optimizer.run_on_dify", autospec=True)
@patch("top_assist.semantic_router.tools.prompt_optimizer.llm_with_schema", autospec=True)
def test_query_prompt_optimizer(
    mock_llm_with_schema: MagicMock,
    mock_run_on_dify: MagicMock,
) -> None:
    # Given
    state = create_state()
    expected_answer = "I am an optimized prompt"
    task_text = "Some task"
    mock_run_on_dify.return_value = expected_answer
    llm_response = mock_llm_with_schema.invoke.return_value = {"task": task_text, "variables": ""}
    prepared_task = cast(PreparedTask, llm_response)

    # When
    result = query_prompt_optimizer.invoke(input={"state": state})

    # Then
    mock_run_on_dify.assert_called_once_with(prepared_task)
    assert isinstance(result, AIMessage)
    assert result.content == expected_answer


@patch("top_assist.semantic_router.tools.prompt_optimizer.llm_with_schema", autospec=True)
def test_query_prompt_optimizer_with_error(mock_llm_with_schema: MagicMock) -> None:
    # Given
    state = create_state()
    expected_answer = FALLBACK_MSG
    mock_llm_with_schema.invoke.side_effect = Exception("Some error")

    # When
    result = query_prompt_optimizer.invoke(input={"state": state})

    # Then
    assert isinstance(result, AIMessage)
    assert result.content == expected_answer


@patch("top_assist.semantic_router.tools.prompt_optimizer.dify_prompt_optimizer_api_key", "some_key")
@patch("top_assist.semantic_router.tools.prompt_optimizer.dify_api_endpoint", "https://some-endpoint.com/api")
def test_run_on_dify() -> None:
    # Given
    prepared_task = PreparedTask(task="Some task", variables="var1,var2")
    expected_result = "This is a new prompt"

    pook.post(
        "https://some-endpoint.com/api",
        headers={
            "Authorization": "Bearer some_key",
            "Content-Type": "application/json",
        },
        json={
            "inputs": {"task": prepared_task.task, "variables": prepared_task.variables},
            "response_mode": "blocking",
            "user": "top_assist",
        },
        reply=200,
        response_json={"data": {"outputs": {"result": expected_result}}},
    )

    # When
    response = run_on_dify(prepared_task=prepared_task)

    # Then
    assert response == expected_result


@patch("top_assist.semantic_router.tools.prompt_optimizer.dify_prompt_optimizer_api_key", "some_key")
@patch("top_assist.semantic_router.tools.prompt_optimizer.dify_api_endpoint", "https://some-endpoint.com/api")
def test_run_on_dify_raises_error_on_non_ok_status() -> None:
    # Given
    prepared_task = PreparedTask(task="Some task", variables="var1,var2")
    response_data = '{"code": "invalid_param", "message": "task is required in input form", "status": 400}'

    pook.post(
        "https://some-endpoint.com/api",
        headers={
            "Authorization": "Bearer some_key",
            "Content-Type": "application/json",
        },
        json={
            "inputs": {"task": prepared_task.task, "variables": prepared_task.variables},
            "response_mode": "blocking",
            "user": "top_assist",
        },
        reply=400,
        response_json=response_data,
    )

    # When / Then
    with pytest.raises(DifyResponseError) as exc_info:
        run_on_dify(prepared_task=prepared_task)

    assert str(exc_info.value) == (f"The error occurred during the Dify response. Details: {response_data}")
