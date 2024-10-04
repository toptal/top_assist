import logging
import time
from collections.abc import Callable, Generator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import TypeVar

from top_assist.configuration import (
    embedding_chunk_size,
    embedding_chunk_sleep_seconds,
    embedding_model_id,
    embedding_workers_num,
    qdrant_url,
)
from top_assist.open_ai.embeddings import embed_text

if qdrant_url:
    TYPE = "qdrant"
    from .engines.qdrant import all_embeddings as _all_embeddings
    from .engines.qdrant import count as _count
    from .engines.qdrant import delete_items as _delete_items
    from .engines.qdrant import retrieve_neighbour_ids as _retrieve_neighbour_ids
    from .engines.qdrant import upsert as _upsert
else:
    TYPE = "weaviate"
    from .engines.weaviate import all_embeddings as _all_embeddings
    from .engines.weaviate import count as _count
    from .engines.weaviate import delete_items as _delete_items
    from .engines.weaviate import retrieve_neighbour_ids as _retrieve_neighbour_ids
    from .engines.weaviate import upsert as _upsert

_T = TypeVar("_T")  # mypy: PEP 695 generics are not yet supported

_DEFAULT_CERTAINTY_THRESHOLD = 0.0  # Extract All items by default


class EmtpyEmbeddingError(Exception):
    pass


@dataclass
class ItemToEmbed:
    item_id: str
    content: str


def delete_items(collection_name: str, item_ids: list[str]) -> None:
    _delete_items(collection_name, item_ids)


def import_items(items: list[_T], *, collection_name: str, formatter: Callable[[_T], ItemToEmbed]) -> None:
    id_embedding_pairs = __prepare_embeddings(items, formatter, collection_name)
    __insert_data(id_embedding_pairs, collection_name)


def all_embeddings(collection_name: str) -> dict[str, list[float]]:
    return _all_embeddings(collection_name)


def count(collection_name: str) -> int:
    return _count(collection_name)


def retrieve_neighbour_ids(
    query: str, *, collection_name: str, count: int, certainty_threshold: float = _DEFAULT_CERTAINTY_THRESHOLD
) -> list[str]:
    try:
        query_embedding = embed_text(text=query, model=embedding_model_id)
    except Exception:
        logging.exception("Error generating query embedding", extra={"collection_name": collection_name})
        raise

    try:
        item_ids = _retrieve_neighbour_ids(collection_name, query_embedding, count, certainty_threshold)
    except Exception:
        logging.exception("Error retrieving relevant IDs", extra={"collection_name": collection_name})
        raise

    return item_ids


__all__ = [
    "TYPE",
    "import_items",
    "all_embeddings",
    "retrieve_neighbour_ids",
    "ItemToEmbed",
    "EmtpyEmbeddingError",
    "delete_items",
]


def __chunks_generator(items: list[_T], chunk_size: int) -> Generator[list[_T], None, None]:
    for i in range(0, len(items), chunk_size):
        yield items[i : i + chunk_size]


def __prepare_embeddings(
    items: list[_T], formatter: Callable[[_T], ItemToEmbed], collection_name: str
) -> list[tuple[str, list[float]]]:
    def worker(item: _T) -> tuple[str, list[float]]:
        formatted = formatter(item)
        log_extra = {"collection_name": collection_name, "item_id": formatted.item_id}
        item_id = formatted.item_id
        content = formatted.content
        content = content[:8190]  # Ensure the content does not exceed the maximum token limit

        try:
            embedding = embed_text(text=content, model=embedding_model_id)
        except Exception:
            logging.exception("Error generating embedding", extra=log_extra)
            raise

        if not embedding or len(embedding) == 0:
            logging.error("Embedding is empty", extra=log_extra)
            raise EmtpyEmbeddingError

        logging.debug("Embedding prepared", extra=log_extra)
        return item_id, embedding

    with ThreadPoolExecutor(max_workers=embedding_workers_num) as executor:
        id_embedding_pairs: list[tuple[str, list[float]]] = []
        for chunk in __chunks_generator(items, embedding_chunk_size):
            if id_embedding_pairs:
                logging.info(
                    "Sleeping before next chunk",
                    extra={"collection_name": collection_name, "time": embedding_chunk_sleep_seconds},
                )
                time.sleep(embedding_chunk_sleep_seconds)
            id_embedding_pairs.extend(executor.map(worker, chunk))
        return id_embedding_pairs


def __insert_data(id_embedding_pairs: list[tuple[str, list[float]]], collection_name: str) -> None:
    logging.info(
        "Adding embeddings to collection...",
        extra={"num": len(id_embedding_pairs), "collection_name": collection_name},
    )
    try:
        new_total = _upsert(collection_name, id_embedding_pairs)
        logging.info(
            "Successfully added embeddings to collection",
            extra={
                "num": len(id_embedding_pairs),
                "collection_name": collection_name,
                "collection_total": new_total,
            },
        )

    except Exception:
        logging.exception("Error adding items to the collection", extra={"collection_name": collection_name})
        raise
