import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

from pydantic import BaseModel

from top_assist.configuration import cryptography_secret_key
from top_assist.utils.cypher import Cypher
from top_assist.utils.sentry_notifier import sentry_notify_exception


class SignInContext:
    def __init__(self, slack_user_id: str, encrypted_state: str):
        self.slack_user_id = slack_user_id
        self.encrypted_state = encrypted_state


_T = TypeVar("_T")  # mypy: PEP 695 generics are not yet supported

AnyBaseModel = TypeVar("AnyBaseModel", bound=BaseModel)


def register_sign_in_context_operation(klass: type[AnyBaseModel], resume_func: Callable[[AnyBaseModel], None]) -> None:
    _operations_registry[klass.__name__] = _RegisteredOperation(
        parser=klass.model_validate,
        resume_func=resume_func,
    )


def sign_in_context_from_operation(slack_user_id: str, operation: BaseModel) -> SignInContext:
    klass = type(operation)
    if klass.__name__ not in _operations_registry:
        raise NotImplementedError("Please register the operation class with register_sign_in_context_operation")

    return __make_context(slack_user_id, __dump_operation(operation))


def validate_operation_class(klass: type[BaseModel]) -> None:
    if klass.__name__ not in _operations_registry:
        raise NotImplementedError("Please register the operation class with register_sign_in_context_operation")


class AuthCallback:
    def __init__(self, function: Callable[[_T], None], arg: _T):
        self.function = function
        self.arg = arg


@dataclass
class ValidAuthState:
    slack_user_id: str
    resume_operation: AuthCallback


@dataclass
class ExpiredAuthState:
    slack_user_id: str
    state_for_retry: SignInContext


def parse_auth_request_state(encrypted_state: str) -> ValidAuthState | ExpiredAuthState:
    decrypted_state = _cypher.decrypt(encrypted_state)
    payload = _Payload.model_validate_json(decrypted_state)

    is_expired = datetime.now(UTC) > datetime.fromisoformat(payload.expires_at)

    if is_expired:
        return ExpiredAuthState(
            slack_user_id=payload.slack_user_id,
            state_for_retry=__make_context(payload.slack_user_id, payload.operation),
        )

    resume_operation = __restore_operation(payload.operation)

    return ValidAuthState(
        slack_user_id=payload.slack_user_id,
        resume_operation=resume_operation,
    )


def __make_context(slack_user_id: str, serialized_operation: str) -> SignInContext:
    expires_at = datetime.now(UTC) + timedelta(minutes=5)
    payload = _Payload(
        expires_at=expires_at.isoformat(),
        slack_user_id=slack_user_id,
        operation=serialized_operation,
    )
    encrypted_state = _cypher.encrypt(payload.model_dump_json())
    return SignInContext(slack_user_id, encrypted_state)


class _Payload(BaseModel):
    expires_at: str
    slack_user_id: str
    operation: str


class OperationUsesReservedFieldError(ValueError):
    pass


def __dump_operation(operation: BaseModel) -> str:
    result = operation.model_dump(mode="json")
    if "__class" in result:
        raise OperationUsesReservedFieldError

    result["__class"] = operation.__class__.__name__
    return json.dumps(result)


def __restore_operation(serialized_operation: str) -> AuthCallback:
    try:
        data = json.loads(serialized_operation)
        desc = _operations_registry[data["__class"]]
        obj: BaseModel = desc.parser(data)
        return AuthCallback(function=desc.resume_func, arg=obj)

    except Exception as e:
        logging.exception("Failed to deserialize SignInContext operation", extra={"error": str(e)})
        sentry_notify_exception(e)
        return AuthCallback(function=lambda _: None, arg=None)


@dataclass
class _RegisteredOperation:
    parser: Callable[[Any], AnyBaseModel]
    resume_func: Callable[[AnyBaseModel], None]


_cypher = Cypher(secret_key=cryptography_secret_key)
_operations_registry = dict[str, _RegisteredOperation]()
