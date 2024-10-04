import threading
from datetime import timedelta
from unittest.mock import MagicMock, create_autospec, patch

from top_assist.utils.scheduler import call_with_delay


@patch("threading.Timer", autospec=True)
def test_call_with_delay(mock_timer: MagicMock) -> None:
    def my_function(_answer_of_life: int) -> None:
        pass

    mock_thread = create_autospec(threading.Thread)
    mock_timer.return_value = mock_thread

    wrapped_function = lambda: my_function(42)
    call_with_delay(interval=timedelta(seconds=2), function=wrapped_function)

    mock_timer.assert_called_once_with(2.0, wrapped_function)
    mock_thread.start.assert_called_once()
    mock_thread.start.reset_mock()
