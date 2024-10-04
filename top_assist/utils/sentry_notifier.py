import logging
from dataclasses import dataclass
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from top_assist.configuration import environment, sentry_dsn


def configure_sentry() -> None:
    if sentry_dsn in (None, ""):
        sentry_sdk.init(dsn="")
        _status.enabled = False
    else:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            profiles_sample_rate=1.0,
            integrations=[
                LoggingIntegration(  # https://docs.sentry.io/platforms/python/integrations/logging/
                    level=logging.INFO,  # level to capture as breadcrumbs
                    event_level=None,  # level to capture as events (If a value of None occurs, the SDK won't send log records as events.)
                )
            ],
        )
        _status.enabled = True


def is_enabled() -> bool:
    return _status.enabled


def sentry_notify_exception(
    exception: Exception,
    *,
    extra: dict[str, Any] | None = None,
    tags: dict[str, Any] | None = None,
) -> None:
    if not _status.enabled:
        return

    with sentry_sdk.push_scope() as scope:
        for k, v in (tags or {}).items():
            scope.set_tag(k, v)
        scope.update_from_kwargs(extras=extra)
        sentry_sdk.capture_exception(exception, scope=scope)
        sentry_sdk.flush()


def sentry_notify_issue(
    message: str,
    *,
    extra: dict[str, Any] | None = None,
    tags: dict[str, Any] | None = None,
) -> None:
    if not _status.enabled:
        return

    with sentry_sdk.push_scope() as scope:
        for k, v in (tags or {}).items():
            scope.set_tag(k, v)
        scope.update_from_kwargs(extras=extra)
        sentry_sdk.capture_message(message, level="error", scope=scope)
        sentry_sdk.flush()


@dataclass
class _Status:
    enabled: bool = False


_status = _Status()
