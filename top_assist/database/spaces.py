import logging
from datetime import datetime

import top_assist.database.pages as db_pages
from top_assist.database.pages import RemovedPages
from top_assist.models.base import int_pk
from top_assist.models.space import SpaceDTO, SpaceORM

from .database import Session, get_db_session


class SpaceNotFoundError(Exception):  # noqa: D101
    def __init__(self, space_id: int_pk):
        super().__init__(f"Space with id {space_id} not found in the database")


def find_or_create(*, space_key: str, space_name: str) -> SpaceDTO:
    """Find or create a space in the database."""
    with get_db_session() as session:
        space = session.query(SpaceORM).filter_by(space_key=space_key).first()
        if space:
            space.space_name = space_name
            return SpaceDTO.from_orm(space)

        new_space = SpaceORM(
            space_key=space_key,
            space_name=space_name,
        )
        session.add(new_space)
        session.flush()  # Flush to get the ID

        logging.info("Added space record", extra={"space_key": space_key})
        return SpaceDTO.from_orm(new_space)


def mark_imported(space: SpaceDTO, import_date: datetime) -> None:
    """Update last import timestamp for the space in the database."""
    with get_db_session() as session:
        record = session.get(SpaceORM, space.id)
        if not record:
            raise SpaceNotFoundError(space.id)

        record.last_import_date = import_date
        space.last_import_date = import_date
        logging.info("Space marked as imported", extra={"space_key": record.space_key, "import_date": import_date})


def all_spaces() -> list[SpaceDTO]:
    """Retrieve all spaces from the database."""
    with get_db_session() as session:
        records = session.query(SpaceORM).all()
        return [SpaceDTO.from_orm(record) for record in records]


def delete_space_and_related_pages(space_id: int) -> RemovedPages:
    with get_db_session() as session:
        space = delete_by_space_id(session, space_id)
        removed_pages = db_pages.delete_by_space(session, space)
        logging.info(
            "Space deleted with pages and embeddings",
            extra={"space_id": space_id, "space_key": space.key, "pages_removed": removed_pages.removed_count},
        )
    return removed_pages


def delete_by_space_id(session: Session, space_id: int) -> SpaceDTO:
    record = session.query(SpaceORM).filter_by(id=space_id).first()
    if not record:
        raise SpaceNotFoundError(space_id)

    space = SpaceDTO.from_orm(record)
    session.delete(record)
    logging.info("Space record deleted", extra={"space_key": space.key})
    return space
