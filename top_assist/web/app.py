import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from top_assist.configuration import api_docs_url, api_host, api_port, api_redocs_url, environment
from top_assist.web.admin import setup_admin_panel
from top_assist.web.router import router

app = FastAPI(docs_url=api_docs_url, redoc_url=api_redocs_url)
setup_admin_panel(app)
app.include_router(router)

app.mount("/static", StaticFiles(directory="top_assist/web/static"), name="static")


def serve() -> None:
    """Entry point for starting the FastAPI application."""
    Instrumentator().instrument(app)
    uvicorn.run(
        "top_assist.web.app:app",
        host=api_host,
        port=api_port,
        reload=(environment == "development"),
        # These two are needed to serve statics with the same
        # protocol as the one used for the page itself
        # See https://jowilf.github.io/starlette-admin/deployment/
        forwarded_allow_ips="*",
        proxy_headers=True,
    )
