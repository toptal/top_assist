import json
from typing import Any

import pytest
from freezegun import freeze_time
from pydantic import BaseModel

from top_assist.auth._sign_in_context import (
    OperationUsesReservedFieldError,
    register_sign_in_context_operation,
    sign_in_context_from_operation,
)
from top_assist.chat_bot.tasks.question import QuestionEvent


@freeze_time("2021-10-01T00:00:00+00:00")
def test_sign_in_context_from_operation() -> None:
    # Given
    operation = QuestionEvent(
        text="test_text",
        ts="test_ts",
        thread_ts="test_thread_ts",
        channel="test_channel",
        is_dm=True,
        user="U123456",
    )

    # When
    result = sign_in_context_from_operation("U123456", operation)

    # Then
    assert result.slack_user_id == "U123456"
    assert result.encrypted_state.startswith("fake_encrypted_")
    assert json.loads(result.encrypted_state.removeprefix("fake_encrypted_")) == {
        "expires_at": "2021-10-01T00:05:00+00:00",
        "slack_user_id": "U123456",
        "operation": json.dumps({
            "text": "test_text",
            "ts": "test_ts",
            "thread_ts": "test_thread_ts",
            "channel": "test_channel",
            "is_dm": True,
            "user": "U123456",
            "__class": "QuestionEvent",
        }),
    }


class UnknownOperation(BaseModel):
    something: str


def test_sign_in_context_from_operation_with_unknown_operation() -> None:
    # Given
    operation = UnknownOperation(something="test_something")

    # When
    with pytest.raises(NotImplementedError) as exc_info:
        sign_in_context_from_operation("U123456", operation)

    # Then
    assert str(exc_info.value) == "Please register the operation class with register_sign_in_context_operation"


class OperationWithConflictingField(BaseModel):
    something: str

    # Pydantic BaseModel does not serialize __class field
    # so model_dump is overriden to reproduce the issue
    def model_dump(self, **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        result = super().model_dump(**kwargs)
        result["__class"] = "test_class"
        return result


def resume_operation_with_conflicting_field(_operation: OperationWithConflictingField) -> None:
    raise NotImplementedError


register_sign_in_context_operation(OperationWithConflictingField, resume_operation_with_conflicting_field)


def test_sign_in_context_from_operation_with_conflicting_operation_field() -> None:
    # Given
    operation = OperationWithConflictingField(something="test_something")

    # When
    with pytest.raises(OperationUsesReservedFieldError) as exc_info:
        sign_in_context_from_operation("U123456", operation)

    # Then
    assert exc_info
