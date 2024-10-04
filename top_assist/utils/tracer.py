from enum import Enum

from ddtrace import tracer as dd_tracer

from top_assist.configuration import dd_log_injection


class ServiceNames(str, Enum):
    """Mapping of service names to be used in Datadog traces."""

    # Main processes
    cli = "top-assist-cli"
    main_menu = "top-assist-main_menu"
    chat_bot = "top-assist-chat-bot"
    web = "top-assist-web"  # not used explicitly, configured in DD_SERVICE_MAPPING env

    # Others
    slack = "top-assist-slack"
    vector_db = "top-assist-vector-db"
    confluence = "top-assist-confluence"
    knowledge_base = "top-assist-knowledge-base"
    open_ai = "top-assist-open-ai"


def initialize_dd_tracer() -> None:
    import ddtrace.auto  # noqa: F401 (we need to import this to autoload built-in instrumentations)


def enabled() -> bool:
    return dd_tracer.enabled


def log_injection_enabled() -> bool:
    return dd_log_injection


initialize_dd_tracer()

tracer = dd_tracer
