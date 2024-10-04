import logging

from top_assist.configuration import logs_file, logs_format, logs_level

from .json_formatter import JSONFormatter
from .text_formatter import TextFormatter


class UnknownFormatError(ValueError):  # noqa: D101
    def __init__(self, name: str):
        expected = ", ".join(_FORMATTERS.keys())
        super().__init__(f"Unknown logging format: '{name}'. Expected one of: {expected}")


def configure_logging() -> None:
    handler = __handler(logs_file)
    handler.formatter = __formatter(logs_format)
    logging.basicConfig(
        force=True,
        handlers=[handler],
        level=logs_level,
    )


def __handler(logs_file: str | None) -> logging.Handler:
    if logs_file is None:
        return logging.StreamHandler()
    else:
        return logging.FileHandler(logs_file)


def __json_formatter() -> logging.Formatter:
    # No need to handle Datadog log injection for JSONFormatter as it includes extra fields automatically
    return JSONFormatter()


def __text_formatter() -> logging.Formatter:
    return TextFormatter()


def __formatter(name: str) -> logging.Formatter:
    factory = _FORMATTERS.get(name)
    if factory is None:
        raise UnknownFormatError(name)

    return factory()


_FORMATTERS = {
    "jsonl": __json_formatter,
    "text": __text_formatter,
}
