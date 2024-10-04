from collections.abc import Callable
from dataclasses import dataclass

import pytest

import top_assist.database._vector.engines.qdrant as qdrant_impl
import top_assist.database._vector.engines.weaviate as weaviate_impl
from tests.utils.vector.qdrant import delete_all_collections as qdrant_delete_all_collections
from tests.utils.vector.weaviate import delete_all_collections as weaviate_delete_all_collections


@dataclass
class VectorEngine:
    upsert: Callable[[str, list[tuple[str, list[float]]]], int]
    all_embeddings: Callable[[str], dict[str, list[float]]]
    count: Callable[[str], int]
    delete_items: Callable[[str, list[str]], None]
    retrieve_neighbour_ids: Callable[[str, list[float], int, float], list[str]]
    internal_name: Callable[[str], str]
    delete_all_collections: Callable[[], None]
    collections_prefix: str


WeaviateEngine = VectorEngine(
    upsert=weaviate_impl.upsert,
    all_embeddings=weaviate_impl.all_embeddings,
    count=weaviate_impl.count,
    delete_items=weaviate_impl.delete_items,
    retrieve_neighbour_ids=weaviate_impl.retrieve_neighbour_ids,
    internal_name=weaviate_impl.__internal_name,  # noqa: SLF001
    delete_all_collections=weaviate_delete_all_collections,
    collections_prefix=weaviate_impl.vector_collections_prefix,
)

QdrantEngine = VectorEngine(
    upsert=qdrant_impl.upsert,
    all_embeddings=qdrant_impl.all_embeddings,
    count=qdrant_impl.count,
    delete_items=qdrant_impl.delete_items,
    retrieve_neighbour_ids=qdrant_impl.retrieve_neighbour_ids,
    internal_name=qdrant_impl.__internal_name,  # noqa: SLF001
    delete_all_collections=qdrant_delete_all_collections,
    collections_prefix=qdrant_impl.vector_collections_prefix,
)


@pytest.fixture(scope="module", params=[WeaviateEngine, QdrantEngine], ids=["weaviate", "qdrant"])
def vector_engine(request: pytest.FixtureRequest) -> VectorEngine:
    return request.param


# Weaviate stores and returns vectors as is, but Qdrant normalizes them
# so to have a universal test, we normalize vectors here
VEC_1_2_3 = [0.26726124, 0.5345225, 0.80178374]  # normalized [1.0, 2.0, 3.0]
VEC_4_5_6 = [0.45584232, 0.5698029, 0.68376344]  # normalized [4.0, 5.0, 6.0]
VEC_7_8_9 = [0.50257070, 0.5743665, 0.64616233]  # normalized [7.0, 8.0, 9.0]
VEC_6_2_3 = [0.85714287, 0.2857143, 0.42857143]  # normalized [6.0, 2.0, 3.0]
VEC_9_5_3 = [0.83925430, 0.4662524, 0.27975145]  # normalized [9.0, 5.0, 3.0]


def test_upsert_and_all_embeddings(vector_engine: VectorEngine) -> None:
    collection_name = "test_collection"

    vector_engine.delete_all_collections()

    id_embedding_pairs = [
        ("1", VEC_1_2_3),
        ("2", VEC_4_5_6),
    ]
    assert vector_engine.upsert(collection_name, id_embedding_pairs) == 2
    assert vector_engine.all_embeddings(collection_name) == {
        "1": pytest.approx(VEC_1_2_3),
        "2": pytest.approx(VEC_4_5_6),
    }
    assert vector_engine.count(collection_name) == 2

    id_embedding_pairs = [
        ("2", VEC_6_2_3),
        ("3", VEC_7_8_9),
    ]
    assert vector_engine.upsert(collection_name, id_embedding_pairs) == 3
    assert vector_engine.all_embeddings(collection_name) == {
        "1": pytest.approx(VEC_1_2_3),
        "2": pytest.approx(VEC_6_2_3),
        "3": pytest.approx(VEC_7_8_9),
    }
    assert vector_engine.count(collection_name) == 3


def test_delete_items(vector_engine: VectorEngine) -> None:
    collection_name = "test_collection"

    vector_engine.delete_all_collections()

    data = [
        ("1", VEC_1_2_3),
        ("2", VEC_4_5_6),
        ("3", VEC_7_8_9),
        ("4", VEC_9_5_3),
    ]
    vector_engine.upsert(collection_name, data)
    assert vector_engine.count(collection_name) == 4

    vector_engine.delete_items(collection_name, ["2", "3"])
    assert vector_engine.all_embeddings(collection_name) == {
        "1": pytest.approx(VEC_1_2_3),
        "4": pytest.approx(VEC_9_5_3),
    }
    assert vector_engine.count(collection_name) == 2


def test_retrieve_neighbour_ids(vector_engine: VectorEngine) -> None:
    collection_name = "test_collection"
    certainty_threshold = 0.0

    vector_engine.delete_all_collections()

    id_embedding_pairs = [
        ("1", VEC_1_2_3),
        ("2", VEC_4_5_6),
        ("3", VEC_7_8_9),
    ]
    vector_engine.upsert(collection_name, id_embedding_pairs)

    query_embedding = VEC_1_2_3
    count = 2
    assert vector_engine.retrieve_neighbour_ids(collection_name, query_embedding, count, certainty_threshold) == [
        "1",
        "2",
    ]

    query_embedding = VEC_1_2_3
    count = 3
    assert vector_engine.retrieve_neighbour_ids(collection_name, query_embedding, count, certainty_threshold) == [
        "1",
        "2",
        "3",
    ]

    query_embedding = VEC_7_8_9
    count = 2
    assert vector_engine.retrieve_neighbour_ids(collection_name, query_embedding, count, certainty_threshold) == [
        "3",
        "2",
    ]

    query_embedding = VEC_7_8_9
    count = 3
    assert vector_engine.retrieve_neighbour_ids(collection_name, query_embedding, count, certainty_threshold) == [
        "3",
        "2",
        "1",
    ]

    query_embedding = VEC_7_8_9
    count = 2
    # Weaviate: [1.0, 0.9990954399108887, 0.9797059297561646]
    # Qdrant: [1.0, 0.9981909, 0.9594119]
    certainty_threshold = 0.98  # Cut off the last element
    assert vector_engine.retrieve_neighbour_ids(collection_name, query_embedding, count, certainty_threshold) == [
        "3",
        "2",
    ]


# it is an internal method, but is a crucial part of behavior
def test_internal_name(vector_engine: VectorEngine) -> None:
    collection_name = "test_collection"

    internal_collection_name = vector_engine.internal_name(collection_name)

    assert collection_name != internal_collection_name
    assert collection_name in internal_collection_name
    assert vector_engine.collections_prefix in internal_collection_name
