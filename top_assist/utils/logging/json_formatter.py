# This is a custom formatter to prepare logs in JSON format for Kibana.
# It allows us to use any extra fields for logging like {"thread_id": thread_id}.
# It also prepares a nice readable format for exceptions and traces.

import datetime as dt
import json
import logging
from typing import Any, override

LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for logging."""

    @override
    def format(self, record: logging.LogRecord) -> str:
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: logging.LogRecord) -> dict[str, Any]:
        message = {
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(record.created, tz=dt.UTC).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "pathname": record.pathname,
            "line_number": record.lineno,
            "filename": record.filename,
            "logger_name": record.name,
            "process": record.process,
            "process_name": record.processName,
        }

        # Pretty print the exception information "exc_info=True"
        if record.exc_info is not None:
            message["exc_info"] = self.formatException(record.exc_info)

        # Pretty print the stack information when "stack_info=True"
        if record.stack_info is not None:
            message["stack_info"] = self.formatStack(record.stack_info)

        # Add any extra attributes to the log message
        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val

        return message
