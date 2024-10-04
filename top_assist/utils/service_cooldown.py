import abc
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from top_assist.configuration import (
    service_cooldown_exp_base,
    service_cooldown_initial_seconds,
    service_cooldown_max_attempts,
    service_cooldown_recovery_factor,
)


class ServiceCooldownState(BaseModel):  # noqa: D101
    timestamp: datetime
    cooldown_seconds: float


class ServiceCooldownStorage(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def write(self, service_key: str, cooldown: float) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def read(self, service_key: str) -> ServiceCooldownState | None:
        raise NotImplementedError


def configure_service_cooldown(storage: ServiceCooldownStorage) -> None:
    _config.storage = storage


def with_service_cooldown(
    *, service_key: str, is_rate_limit_error: Callable[[Any], bool]
) -> Callable[[Callable], Callable]:
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Callable:  # noqa: ANN401
            attempt = 1
            pause_seconds = __pause_seconds_from_state(_config.storage.read(service_key))
            while True:
                try:
                    if pause_seconds > 0:
                        __log_backoff(service_key, pause_seconds)
                        time.sleep(pause_seconds)

                    return func(*args, **kwargs)

                except Exception as e:
                    if not is_rate_limit_error(e):
                        raise

                    __log_attempt_error(service_key, e)

                    if attempt >= _config.max_attempts:
                        __log_give_up(service_key, pause_seconds)
                        raise

                    attempt += 1
                    pause_seconds = __next_pause_seconds(pause_seconds)
                    _config.storage.write(service_key, pause_seconds)

        return wrapper

    return decorator


def __log_backoff(service_key: str, seconds: float) -> None:
    logging.warning(
        "Service cooldown backoff",
        extra={"service_key": service_key, "seconds": seconds},
    )


def __log_attempt_error(service_key: str, error: Exception) -> None:
    logging.warning(
        "Service cooldown rate limit error",
        extra={"service_key": service_key, "error": error},
    )


def __log_give_up(service_key: str, seconds: float) -> None:
    logging.error(
        "Service cooldown give up",
        extra={"service_key": service_key, "seconds": seconds},
    )


def __pause_seconds_from_state(state: ServiceCooldownState | None) -> float:
    if state is None:
        return 0

    seconds_passed = (datetime.now(UTC) - state.timestamp).total_seconds()
    return state.cooldown_seconds - _config.recovery_factor * seconds_passed


def __next_pause_seconds(pause_seconds: float) -> float:
    return max(
        pause_seconds * _config.exp_base,
        _config.initial_seconds,
    )


class _DummyServiceCooldownStorage(ServiceCooldownStorage):
    def write(self, _service_key: str, _cooldown: float) -> None:
        pass

    def read(self, _service_key: str) -> ServiceCooldownState | None:
        return None


@dataclass
class _Config:
    storage: ServiceCooldownStorage
    recovery_factor = service_cooldown_recovery_factor
    exp_base = service_cooldown_exp_base
    initial_seconds = service_cooldown_initial_seconds
    max_attempts = service_cooldown_max_attempts


_config = _Config(_DummyServiceCooldownStorage())
