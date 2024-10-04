from typing import TYPE_CHECKING

from top_assist.database._vector.engines.qdrant import __get_client, vector_collections_prefix

if TYPE_CHECKING:
    from qdrant_client import QdrantClient


def delete_all_collections() -> None:
    client: QdrantClient = __get_client()
    for collection in client.get_collections().collections:
        if collection.name.startswith(vector_collections_prefix):
            client.delete_collection(collection.name)
