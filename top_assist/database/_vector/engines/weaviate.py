import logging
from uuid import UUID

import weaviate
import weaviate.classes as wvc

from top_assist.configuration import (
    vector_collections_prefix,
    weaviate_api_key,
    weaviate_client_skip_init_checks,
    weaviate_grpc_host,
    weaviate_grpc_port,
    weaviate_http_host,
    weaviate_http_port,
    weaviate_secure,
)


class CollectionDoesNotExistError(Exception):
    def __init__(self, collection_name: str):
        super().__init__(f"`{collection_name}` collection does not exist, did you import the related data?")


def upsert(collection_name: str, id_embedding_pairs: list[tuple[str, list[float]]]) -> int:
    """Upsert the given embeddings into the specified collection in the vector database.

    Returns:
        int: The number of points in the collection after upserting the embeddings.
    """
    original_name = collection_name
    collection_name = __internal_name(collection_name)
    with __get_client() as client:
        collection = __ensure_collection(collection_name, original_name, client)

        data = [
            wvc.data.DataObject(
                uuid=UUID(int=int(external_id)),
                vector=embedding,
            )
            for external_id, embedding in id_embedding_pairs
        ]

        collection.data.insert_many(data)
        return len(collection)


def retrieve_neighbour_ids(
    collection_name: str, query_embedding: list[float], count: int, certainty_threshold: float
) -> list[str]:
    """Retrieve the IDs of the most similar points to the given query embedding in the collection."""
    collection_name = __internal_name(collection_name)
    with __get_client() as client:
        if not client.collections.exists(collection_name):
            raise CollectionDoesNotExistError(collection_name)

        collection = client.collections.get(collection_name)

        points = collection.query.near_vector(
            near_vector=query_embedding,
            limit=count,
            certainty=certainty_threshold,
            return_metadata=wvc.query.MetadataQuery(certainty=True),
        )
        logging.debug("Similar points certainty", extra={"points": [p.metadata.certainty for p in points.objects]})

        return [str(p.uuid.int) for p in points.objects]


def all_embeddings(collection_name: str) -> dict[str, list[float]]:
    """Retrieve all embeddings from the specified collection in the vector database.

    Returns:
        Dict[str, List[float]]: A dictionary mapping IDs to embeddings.
    """
    collection_name = __internal_name(collection_name)
    embeddings: dict[str, list[float]] = {}
    with __get_client() as client:
        if not client.collections.exists(collection_name):
            return embeddings

        collection = client.collections.get(collection_name)
        for record in collection.iterator(include_vector=True):
            embeddings[str(record.uuid.int)] = record.vector["default"]

    return embeddings


def count(collection_name: str) -> int:
    collection_name = __internal_name(collection_name)
    with __get_client() as client:
        if not client.collections.exists(collection_name):
            return 0

        collection = client.collections.get(collection_name)
        return collection.aggregate.over_all(total_count=True).total_count


def delete_items(collection_name: str, item_ids: list[str]) -> None:
    collection_name = __internal_name(collection_name)
    with __get_client() as client:
        collection = client.collections.get(collection_name)
        uuid_list = [UUID(int=item) for item in [int(item) for item in item_ids]]
        collection.data.delete_many(where=wvc.query.Filter.by_id().contains_any(uuid_list))


def __get_client() -> weaviate.WeaviateClient:
    return weaviate.connect_to_custom(
        http_host=weaviate_http_host,
        http_port=weaviate_http_port,
        http_secure=weaviate_secure,
        grpc_host=weaviate_grpc_host,
        grpc_port=weaviate_grpc_port,
        grpc_secure=weaviate_secure,
        auth_credentials=(wvc.init.Auth.api_key(weaviate_api_key) if weaviate_api_key else None),
        skip_init_checks=weaviate_client_skip_init_checks,
    )


def __ensure_collection(
    internal_name: str,
    original_name: str,
    client: weaviate.WeaviateClient,
) -> weaviate.collections.Collection:
    if client.collections.exists(internal_name):
        return client.collections.get(internal_name)

    log_extra = {"collection_name": original_name, "internal_name": internal_name}
    logging.info("Collection does not exist. Creating it...", extra=log_extra)

    collection = client.collections.create(
        name=internal_name,
        vectorizer_config=wvc.config.Configure.Vectorizer.none(),
        vector_index_config=wvc.config.Configure.VectorIndex.hnsw(
            distance_metric=wvc.config.VectorDistances.COSINE,
        ),
    )
    logging.info("Collection created", extra=log_extra)
    return collection


def __internal_name(collection_name: str) -> str:
    return f"{vector_collections_prefix}_{collection_name}"
