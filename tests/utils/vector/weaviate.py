from top_assist.database._vector.engines.weaviate import __get_client, vector_collections_prefix


def delete_all_collections() -> None:
    with __get_client() as client:
        for collection in client.collections.list_all():
            if collection.startswith(vector_collections_prefix):
                client.collections.delete(collection)
