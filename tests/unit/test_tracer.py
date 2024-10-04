from unittest.mock import patch

from top_assist.utils.tracer import enabled, log_injection_enabled


def test_enabled() -> None:
    with patch("top_assist.utils.tracer.dd_tracer.enabled", new=True):
        assert enabled()

    assert not enabled()


def test_log_injection_enabled() -> None:
    with patch("top_assist.utils.tracer.dd_log_injection", new=True):
        assert log_injection_enabled()

    assert not log_injection_enabled()
