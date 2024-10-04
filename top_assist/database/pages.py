import logging
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from top_assist.models.page_data import PageDataDTO, PageDataORM
from top_assist.models.space import SpaceDTO

from ._vector import pages as vector_pages
from .database import get_db_session


@dataclass
class RemovedPages:  # noqa: D101
    removed_count: int


def upsert_many(space: SpaceDTO, pages: list[PageDataDTO]) -> None:
    __upsert_records(space, pages)
    vector_pages.import_data(pages)


def delete_by_page_ids(page_ids: list[str]) -> RemovedPages:
    with get_db_session() as session:
        pages = session.query(PageDataORM).filter(PageDataORM.page_id.in_(page_ids)).all()
        for page in pages:
            session.delete(page)
        vector_pages.delete_embeddings(page_ids)
        return RemovedPages(removed_count=len(page_ids))


def delete_by_space(session: Session, space: SpaceDTO) -> RemovedPages:
    pages = session.query(PageDataORM).filter_by(space_id=space.id).all()
    page_ids = [page.page_id for page in pages]
    if pages:
        for page in pages:
            session.delete(page)
        vector_pages.delete_embeddings(page_ids)
    return RemovedPages(removed_count=len(page_ids))


def __upsert_records(space: SpaceDTO, pages: list[PageDataDTO]) -> None:
    with get_db_session() as session:
        for page in pages:
            if page.space_key != space.key:
                raise NotImplementedError(f"Multi-space upsert is not supported: {page.space_key} != {space.key}")

            page_id = page.page_id
            old_page = session.query(PageDataORM).filter_by(page_id=page_id).first()
            if old_page:
                old_page.title = page.title
                old_page.last_updated = page.last_updated
                old_page.content = page.content
                old_page.comments = page.comments
                old_page.space_id = space.id
                old_page.space_key = space.key
                logging.info("Update page record", extra={"space_key": old_page.space_key, "page_id": page_id})
            else:
                new_page = PageDataORM(
                    page_id=page_id,
                    space_key=space.key,
                    space_id=space.id,
                    title=page.title,
                    author=page.author,
                    created_date=page.created_date,
                    last_updated=page.last_updated,
                    content=page.content,
                    comments=page.comments,
                )
                session.add(new_page)
                logging.info("Add page record", extra={"space_key": space.key, "page_id": page_id})


def retrieve_relevant(question: str, count: int) -> list[PageDataDTO]:
    ids = vector_pages.retrieve_relevant_ids(question, count=count)
    logging.info("Retrieved relevant page ids", extra={"ids": ids})
    return find_many_by_ids(page_ids=ids)


def find_many_by_ids(page_ids: list[str]) -> list[PageDataDTO]:
    with get_db_session() as session:
        records = session.query(PageDataORM).filter(PageDataORM.page_id.in_(page_ids)).all()
        # return ids in the same order as requested
        record_map = {record.page_id: PageDataDTO.from_orm(record) for record in records}
        return [record_map[page_id] for page_id in page_ids if page_id in record_map]


def all_ids_by_space(space: SpaceDTO) -> list[str]:
    with get_db_session() as session:
        records = session.query(PageDataORM).filter_by(space_id=space.id).all()
        return [record.page_id for record in records]


def count_all_by_space(space: SpaceDTO) -> int:
    with get_db_session() as session:
        return session.query(func.count(PageDataORM.id)).filter_by(space_id=space.id).scalar()


def all_embeddings() -> dict[str, list[float]]:
    return vector_pages.all_embeddings()


def count_embeddings() -> int:
    return vector_pages.count()
