import logging

from top_assist.configuration import logs_text_color_enable

from .json_formatter import LOG_RECORD_BUILTIN_ATTRS

_TEXT_FMT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s%(extras)s @ %(module)s/%(funcName)s"
_TEXT_FMT_EXCLUDE_FROM_EXTRA = {*LOG_RECORD_BUILTIN_ATTRS, "asctime", "levelname", "module", "funcName", "message"}
_TEXT_DATE_FMT = "%Y-%m-%dT%H:%M:%Sz"

_COLOR_GREY = "\x1b[38;20m"
_COLOR_BOLD_WHITE = "\x1b[1m\x1b[37m"
_COLOR_BLUE = "\x1b[34;20m"
_COLOR_YELLOW = "\x1b[33;20m"
_COLOR_BOLD_RED = "\x1b[1m\x1b[31m"
_COLOR_RED = "\x1b[31;1m"
_COLOR_RESET = "\x1b[0m"

_NAME_FORMATS = {"sqlalchemy.engine.Engine": _COLOR_BOLD_WHITE + _TEXT_FMT + _COLOR_RESET}

_LEVEL_FORMATS = {
    logging.DEBUG: _COLOR_GREY + _TEXT_FMT + _COLOR_RESET,
    logging.INFO: _COLOR_BLUE + _TEXT_FMT + _COLOR_RESET,
    logging.WARNING: _COLOR_YELLOW + _TEXT_FMT + _COLOR_RESET,
    logging.ERROR: _COLOR_RED + _TEXT_FMT + _COLOR_RESET,
    logging.CRITICAL: _COLOR_BOLD_RED + _TEXT_FMT + _COLOR_RESET,
}


class TextFormatter(logging.Formatter):
    """Custom text formatter for logging."""

    def __init__(self):
        super().__init__(fmt=_TEXT_FMT, datefmt=_TEXT_DATE_FMT)

    def format(self, record: logging.LogRecord) -> str:
        values = [f"{key}={value}" for key, value in record.__dict__.items() if key not in _TEXT_FMT_EXCLUDE_FROM_EXTRA]
        record.extras = f" $ {", ".join(values)}" if values else ""

        if not logs_text_color_enable:
            return super().format(record)

        log_fmt = _NAME_FORMATS.get(record.name) if record.name in _NAME_FORMATS else _LEVEL_FORMATS.get(record.levelno)

        formatter = logging.Formatter(fmt=log_fmt, datefmt=self.datefmt)
        return formatter.format(record)
