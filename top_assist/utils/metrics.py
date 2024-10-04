import logging
import socket
from contextlib import closing

from prometheus_client import CollectorRegistry, Counter, Histogram, Summary, start_http_server
from prometheus_client import multiprocess as prometheus_multiprocess

from top_assist.configuration import metrics_port, metrics_port_auto_increment

QUESTION_ASKED_METRIC = Counter(
    name="top_assist_question_asked",
    documentation="Questions sent to TopAssist",
    labelnames=["user"],
)
ANSWER_LATENCY_SUMMARY_METRIC = Summary(
    name="top_assist_answer_latency_summary",
    documentation="Latency of Top Assist answers (seconds)",
    labelnames=["type"],
    unit="seconds",
)
ANSWER_LATENCY_HISTOGRAM_METRIC = Histogram(
    name="top_assist_answer_latency_hist",
    documentation="Latency of Top Assist answers (seconds)",
    labelnames=["type"],
    unit="seconds",
    buckets=[5, 10, 15, 20, 30, 60, 120, 300, float("inf")],
)
ANSWER_USER_FEEDBACK_POSITIVE_METRIC = Counter(
    name="top_assist_answer_user_feedback_positive",
    documentation="User feedback for Top Assist Answer (positive)",
)
ANSWER_USER_FEEDBACK_NEGATIVE_METRIC = Counter(
    name="top_assist_answer_user_feedback_negative",
    documentation="User feedback for Top Assist Answer (negative)",
)
TEST_METRIC = Counter(
    name="top_assist_test",
    documentation="Test Metric",
)
EVENT_LATENCY_SUMMARY_METRIC = Summary(
    name="top_assist_event_latency_summary",
    documentation="Latency in receiving an event sent to Top Assist (in seconds)",
    labelnames=["type"],
    unit="seconds",
)
EVENT_LATENCY_HISTOGRAM_METRIC = Histogram(
    name="top_assist_event_latency_hist",
    documentation="Latency in receiving a event sent to Top Assist (in seconds)",
    labelnames=["type"],
    unit="seconds",
    buckets=[0.25, 0.5, 0.75, 1, 2, 3, 5, 10, 15, 20, 30, 60, 120, 300, float("inf")],
)


def start_metrics_server(
    *,
    port: int = metrics_port,
    multiprocess: bool = False,
    port_auto_increment: bool = metrics_port_auto_increment,
) -> None:
    if port_auto_increment:
        port = __next_available_port(port)
        logging.info("Using Port %s for Metrics", port)
    # Multiprocess Mode has some limitations but is required when using ProcessPoolExecutor, see: https://prometheus.github.io/client_python/multiprocess/
    if multiprocess:
        registry = CollectorRegistry()
        prometheus_multiprocess.MultiProcessCollector(registry)
        start_http_server(port, registry=registry)
        return

    start_http_server(port)


def __next_available_port(port: int) -> int:
    if __is_port_available(port):
        return port

    return __next_available_port(port + 1)


def __is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex((host, port)) != 0
