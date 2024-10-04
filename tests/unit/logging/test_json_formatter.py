import json
from datetime import UTC, datetime
from logging import getLogger

from top_assist.utils.logging.json_formatter import JSONFormatter

logger = getLogger()


def test_format_with_dd() -> None:
    formatter = JSONFormatter()

    record = logger.makeRecord(
        name="test",
        level=10,
        lno=1,
        msg="test",
        args=(),
        exc_info=None,
        fn="test_file.py",  # fn is the pathname
    )
    setattr(record, "dd.trace_id", "123")
    setattr(record, "dd.span_id", "456")
    result = json.loads(formatter.format(record))

    assert result["message"] == "test"
    assert result["level"] == "DEBUG"
    assert result["dd.trace_id"] == "123"
    assert result["dd.span_id"] == "456"


def test_prepare_log_with_extra() -> None:
    formatter = JSONFormatter()
    line_number = 10

    record = logger.makeRecord(
        name="test_logger",
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

    result = json.loads(formatter.format(record))

    assert result["timestamp"] == datetime.fromtimestamp(record.created, tz=UTC).isoformat()
    assert result["level"] == "DEBUG"
    assert result["message"] == "Test message"
    assert result["module"] == "test_file"
    assert result["pathname"] == "my_test/test_file.py"
    assert result["function"] == "test_my_func"
    assert result["line_number"] == line_number
    assert result["logger_name"] == "test_logger"
    assert result["process_name"] == "MainProcess"
    assert result["stack_info"] == "this is a very long stack trace"
    assert result["custom_arg1"] == "value1"
    assert result["custom_arg2"] == "value2"
