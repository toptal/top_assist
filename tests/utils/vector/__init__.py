from top_assist.database._vector.engine import TYPE

if TYPE == "weaviate":
    from .weaviate import delete_all_collections
elif TYPE == "qdrant":
    from .qdrant import delete_all_collections
else:
    raise NotImplementedError(f"Unknown vector engine type: {TYPE}")

__all__ = ["delete_all_collections"]
