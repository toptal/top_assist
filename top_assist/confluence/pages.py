from top_assist.utils.tracer import ServiceNames, tracer

from ._client import ConfluenceClient


@tracer.wrap(service=ServiceNames.confluence.value)
def update_page(page_id: str, title: str, content: str, *, minor_edit: bool) -> dict:
    confluence_client = ConfluenceClient()
    return confluence_client.update_page(
        page_id,
        title,
        content,
        minor_edit=minor_edit,  # do not notify watchers
    )
