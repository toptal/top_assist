from unittest.mock import MagicMock, patch

from top_assist.configuration import metrics_port
from top_assist.utils.metrics import start_metrics_server


@patch("top_assist.utils.metrics.start_http_server")
def test_start_metrics_server_single_process(mock_start_http_server: MagicMock) -> None:
    start_metrics_server(multiprocess=False)
    mock_start_http_server.assert_called_with(metrics_port)


def test_start_metrics_server_multiprocess() -> None:
    mock_registry_instance = MagicMock()
    with (
        patch("top_assist.utils.metrics.start_http_server") as mock_start_http_server,
        patch("top_assist.utils.metrics.CollectorRegistry", return_value=mock_registry_instance),
        patch("top_assist.utils.metrics.prometheus_multiprocess.MultiProcessCollector") as mock_multi_process_collector,
    ):
        start_metrics_server(multiprocess=True)

        mock_multi_process_collector.assert_called_with(mock_registry_instance)
        mock_start_http_server.assert_called_with(metrics_port, registry=mock_registry_instance)


@patch("top_assist.utils.metrics.socket.socket")
def test_start_metrics_server_auto_increment_port(mock_socket: MagicMock) -> None:
    mock_socket_instance = mock_socket.return_value

    with patch("top_assist.utils.metrics.start_http_server") as mock_start_http_server:
        mock_socket_instance.connect_ex.side_effect = [0, 0, 0, 1]
        start_metrics_server(multiprocess=False)

        mock_start_http_server.assert_called_with(9093)


@patch("top_assist.utils.metrics.socket.socket")
def test_start_metrics_server_multiprocess_and_with_autoincrement(mock_socket: MagicMock) -> None:
    mock_registry_instance = MagicMock()
    mock_socket_instance = mock_socket.return_value

    with (
        patch("top_assist.utils.metrics.start_http_server") as mock_start_http_server,
        patch("top_assist.utils.metrics.CollectorRegistry", return_value=mock_registry_instance),
        patch("top_assist.utils.metrics.prometheus_multiprocess.MultiProcessCollector") as mock_multi_process_collector,
    ):
        mock_socket_instance.connect_ex.side_effect = [0, 0, 1]

        start_metrics_server(multiprocess=True)

        mock_multi_process_collector.assert_called_with(mock_registry_instance)
        mock_start_http_server.assert_called_with(9092, registry=mock_registry_instance)
