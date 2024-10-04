import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from top_assist.configuration import qdrant_url, vector_collections_prefix


class CollectionDoesNotExistError(Exception):
    def __init__(self, collection_name: str):
        super().__init__(f"{collection_name} collection does not exist, did you import the related data?")


def upsert(collection_name: str, id_embedding_pairs: list[tuple[str, list[float]]]) -> int:
    """Upsert the given embeddings into the specified collection in the vector database.

    Returns:
        int: The number of points in the collection after upserting the embeddings.
    """
    original_name = collection_name
    collection_name = __internal_name(collection_name)
    client = __get_client()
    vector_size = len(id_embedding_pairs[0][1])
    __ensure_collection(client, collection_name, vector_size)

    points = [
        PointStruct(
            id=int(external_id),
            vector=embedding,
        )
        for external_id, embedding in id_embedding_pairs
    ]

    chunk_size = 100
    for i in range(0, len(points), chunk_size):
        logging.debug(
            "Upserting chunk",
            extra={"i": i, "collection_name": original_name, "internal_name": collection_name},
        )
        chunk = points[i : i + chunk_size]
        client.upsert(collection_name, chunk, wait=True)

    return client.count(collection_name).count


def retrieve_neighbour_ids(
    collection_name: str, query_embedding: list[float], count: int, certainty_threshold: float
) -> list[str]:
    """Retrieve the IDs of the most similar points to the given query embedding in the collection."""
    collection_name = __internal_name(collection_name)
    client = __get_client()

    if not client.collection_exists(collection_name=collection_name):
        raise CollectionDoesNotExistError(collection_name)

    similar_points = client.search(
        collection_name,
        query_embedding,
        limit=count,
        score_threshold=certainty_threshold,
    )
    logging.debug("Similar points scores", extra={"similar_points": [point.score for point in similar_points]})

    return [str(point.id) for point in similar_points]


def all_embeddings(collection_name: str) -> dict[str, list[float]]:
    """Retrieve all embeddings from the specified collection in the vector database.

    Returns:
        Dict[str, List[float]]: A dictionary mapping IDs to embeddings.
    """
    collection_name = __internal_name(collection_name)
    client = __get_client()
    if not client.collection_exists(collection_name):
        return {}

    page_size, offset = 100, None
    result = {}

    while True:
        points, offset = client.scroll(
            collection_name,
            with_vectors=True,
            limit=page_size,
            offset=offset,
        )

        for p in points:
            if not isinstance(p.vector, list):
                raise NotImplementedError("Only list vectors are supported")

            result[str(p.id)] = p.vector

        if not offset:
            break

    return result


def count(collection_name: str) -> int:
    collection_name = __internal_name(collection_name)
    client = __get_client()
    if not client.collection_exists(collection_name):
        return 0

    return client.count(collection_name).count


def delete_items(collection_name: str, item_ids: list[str]) -> None:
    collection_name = __internal_name(collection_name)
    client = __get_client()
    client.delete(collection_name, list(map(int, item_ids)))


def __get_client() -> QdrantClient:
    return QdrantClient(
        url=qdrant_url,
    )


def __ensure_collection(client: QdrantClient, collection_name: str, vector_size: int) -> None:
    if client.collection_exists(collection_name):
        return

    client.create_collection(
        collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )


def __internal_name(collection_name: str) -> str:
    return f"{vector_collections_prefix}_{collection_name}"
