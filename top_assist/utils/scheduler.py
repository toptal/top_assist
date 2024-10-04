import threading
from collections.abc import Callable
from datetime import timedelta


def call_with_delay(interval: timedelta, function: Callable[[], None]) -> None:
    threading.Timer(interval.total_seconds(), function).start()
