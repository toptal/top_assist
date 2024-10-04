import logging
import time
from collections.abc import Generator
from logging import getLogger
from unittest.mock import patch

import pytest

from top_assist.utils.logging.text_formatter import _COLOR_GREY, _COLOR_RESET, TextFormatter

logger = getLogger()


@pytest.fixture(autouse=True)
def _setup_log_config() -> Generator:
    with patch("top_assist.utils.logging.text_formatter.logs_text_color_enable", new=False):
        yield


def ts(record: logging.LogRecord) -> str:
    timestamp = time.localtime(record.created)
    return time.strftime("%Y-%m-%dT%H:%M:%Sz", timestamp)


def test_format_with_dd() -> None:
    formatter = TextFormatter()

    record = logger.makeRecord(
        name="test_name",
        level=10,
        lno=1,
        msg="test_message",
        args=(),
        exc_info=None,
        fn="test_file.py",  # fn is the pathname
    )
    setattr(record, "dd.trace_id", "123")
    setattr(record, "dd.span_id", "456")
    result = formatter.format(record)

    assert result == f"{ts(record)} [DEBUG] [test_name] test_message $ dd.trace_id=123, dd.span_id=456 @ test_file/None"


def test_format_without_extra() -> None:
    formatter = TextFormatter()

    record = logger.makeRecord(
        name="test_name",
        level=10,
        lno=1,
        msg="test_message",
        args=(),
        exc_info=None,
        fn="test_file.py",  # fn is the pathname
    )
    result = formatter.format(record)

    assert result == f"{ts(record)} [DEBUG] [test_name] test_message @ test_file/None"


def test_prepare_log_with_extra() -> None:
    formatter = TextFormatter()
    line_number = 10

    record = logger.makeRecord(
        name="test_name",
        level=10,
        lno=line_number,
        msg="Test message",
        fn="my_test/test_file.py",  # fn is the pathname
        func="test_my_func",
        args=(),
        exc_info=None,
        sinfo="this is a very long stack trace",
        extra={"custom_arg1": "value1", "custom_arg2": "value2"},
    )

    result_lines = formatter.format(record).split("\n")

    assert result_lines == [
        f"{ts(record)} [DEBUG] [test_name] Test message $ custom_arg1=value1, custom_arg2=value2 @ test_file/test_my_func",
        "this is a very long stack trace",
    ]


@patch("top_assist.utils.logging.text_formatter.logs_text_color_enable", new=True)
def test_format_with_colors() -> None:
    formatter = TextFormatter()

    record = logger.makeRecord(
        name="test_name",
        level=10,
        lno=1,
        msg="test_message",
        args=(),
        exc_info=None,
        fn="test_file.py",  # fn is the pathname
    )
    result = formatter.format(record)

    assert result == f"{_COLOR_GREY}{ts(record)} [DEBUG] [test_name] test_message @ test_file/None{_COLOR_RESET}"
