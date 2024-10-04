from top_assist.configuration import pages_certainty_threshold
from top_assist.models.page_data import PageDataDTO
from top_assist.utils.tracer import ServiceNames, tracer

from .engine import ItemToEmbed, delete_items, import_items, retrieve_neighbour_ids
from .engine import all_embeddings as _all_embeddings
from .engine import count as _count

_COLLECTION_NAME = "pages"


@tracer.wrap(service=ServiceNames.vector_db.value, resource="vector.pages.retriever.delete_embeddings")
def delete_embeddings(page_ids: list[str]) -> None:
    """Delete pages from the vector database."""
    delete_items(_COLLECTION_NAME, page_ids)


@tracer.wrap(service=ServiceNames.vector_db.value, resource="vector.pages.importer.import_data")
def import_data(pages: list[PageDataDTO]) -> None:
    """Generate embeddings for Confluence pages and insert them into the vector database."""
    import_items(pages, collection_name=_COLLECTION_NAME, formatter=__format_for_embedding)


@tracer.wrap(service=ServiceNames.vector_db.value, resource="vector.pages.retriever.retrieve_relevant_ids")
def retrieve_relevant_ids(query: str, count: int) -> list[str]:
    """Retrieve page IDs most relevant to the query."""
    return retrieve_neighbour_ids(
        query, collection_name=_COLLECTION_NAME, count=count, certainty_threshold=pages_certainty_threshold
    )


@tracer.wrap(service=ServiceNames.vector_db.value, resource="vector.pages.retriever.all_embeddings")
def all_embeddings() -> dict[str, list[float]]:
    return _all_embeddings(_COLLECTION_NAME)


@tracer.wrap(service=ServiceNames.vector_db.value, resource="vector.pages.retriever.count")
def count() -> int:
    return _count(_COLLECTION_NAME)


def __format_for_embedding(page: PageDataDTO) -> ItemToEmbed:
    return ItemToEmbed(item_id=page.page_id, content=page.format_for_llm())
