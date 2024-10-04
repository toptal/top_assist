from collections.abc import Generator
from unittest.mock import MagicMock, Mock, patch

import pytest

from top_assist.utils.sentry_notifier import configure_sentry, is_enabled, sentry_notify_exception


@pytest.fixture()
def mock_sentry_sdk() -> Generator[MagicMock, None, None]:
    with patch("top_assist.utils.sentry_notifier.sentry_sdk") as mock_sdk:
        yield mock_sdk


def test_initialization_with_dsn() -> None:
    with patch("top_assist.utils.sentry_notifier.sentry_dsn", new="https://123@sentry.io/123"):
        configure_sentry()

        assert is_enabled() is True


def test_initialization_without_dsn() -> None:
    with patch("top_assist.utils.sentry_notifier.sentry_dsn", ""):
        configure_sentry()

        assert is_enabled() is False


def test_notify_exception(mock_sentry_sdk: MagicMock) -> None:
    with (
        patch("top_assist.utils.sentry_notifier.sentry_dsn", "https://123@sentry.io/123"),
        patch("top_assist.utils.sentry_notifier.environment", "test"),
    ):
        mock_scope = Mock()
        mock_sentry_sdk.push_scope.return_value.__enter__.return_value = mock_scope

        test_exception = Exception("Test Exception")
        test_extra = {"extra_key": "extra_value"}
        test_tags = {"tag_key": "tag_value"}

        configure_sentry()
        sentry_notify_exception(test_exception, extra=test_extra, tags=test_tags)

        mock_sentry_sdk.push_scope.assert_called_once()
        mock_sentry_sdk.capture_exception.assert_called_once_with(test_exception, scope=mock_scope)


def test_notify_exception_disabled(mock_sentry_sdk: MagicMock) -> None:
    with patch("top_assist.utils.sentry_notifier.sentry_dsn", ""):
        test_exception = Exception("Test Exception")
        test_extra = {"extra_key": "extra_value"}
        test_tags = {"tag_key": "tag_value"}

        configure_sentry()
        sentry_notify_exception(test_exception, extra=test_extra, tags=test_tags)

        mock_sentry_sdk.push_scope.assert_not_called()
        mock_sentry_sdk.capture_exception.assert_not_called()
