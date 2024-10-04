from top_assist.utils.metrics import start_metrics_server

from .app import serve

start_metrics_server(multiprocess=True)
serve()
