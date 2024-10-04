import logging
from datetime import UTC, datetime, timedelta

import top_assist.database.pages as db_pages
import top_assist.database.spaces as db_spaces
from top_assist.configuration import confluence_ignore_labels
from top_assist.confluence.retriever import (
    InaccessiblePage,
    InaccessibleSpaceError,
    get_space_page_ids,
    get_space_page_ids_by_label,
    retrieve_space,
    retrieve_space_with_date,
)
from top_assist.confluence.spaces import retrieve_space_list
from top_assist.models.page_data import PageDataDTO
from top_assist.models.space import SpaceDTO
from top_assist.utils.sentry_notifier import sentry_notify_issue
from top_assist.utils.tracer import ServiceNames, tracer

_SPACE_STATUS_FOR_IMPORT = "current"
_PAGE_STATUS_FOR_IMPORT = "current"


@tracer.wrap(service=ServiceNames.knowledge_base.value)
def import_confluence_space(
    *,
    space_key: str,
    space_name: str,
    ignore_labels: list[str] = confluence_ignore_labels,
) -> None:
    import_date = datetime.now(UTC)
    ignored_by_label_page_ids = set(get_space_page_ids_by_label(space_key, ignore_labels))
    pages_data_raw = retrieve_space(
        space_key,
        page_status=_PAGE_STATUS_FOR_IMPORT,
        ignored_page_ids=ignored_by_label_page_ids,
    )
    pages_data = __assert_all_pages_accessible(pages_data_raw)

    space = db_spaces.find_or_create(space_key=space_key, space_name=space_name)
    db_pages.upsert_many(space, pages_data)
    db_spaces.mark_imported(space, import_date=import_date)


@tracer.wrap(service=ServiceNames.knowledge_base.value)
def pull_updates() -> None:
    """Pull page updates in imported Confluence spaces that happened since last time."""
    spaces = db_spaces.all_spaces()
    archived_space_keys = [space.key for space in retrieve_space_list(status="archived")]

    if not spaces:
        logging.error("No spaces found in the database")
        return

    for space in spaces:
        if space.key in archived_space_keys:
            __delete_space_and_related_pages(space)
            continue

        try:
            __remove_non_relevant_pages(space)
            update_space(space)

        except InaccessibleSpaceError:
            logging.warning("Space is inaccessible -> removing", extra={"space_key": space.key})
            __delete_space_and_related_pages(space)


def update_space(space: SpaceDTO, ignore_labels: list[str] = confluence_ignore_labels) -> None:
    if not space.last_import_date:
        logging.error("Space has no last import date, skipping", extra={"space_key": space.key})
        sentry_notify_issue("Space has no last import date", extra={"space_key": space.key})
        return

    import_date = datetime.now(UTC)
    updated_pages_raw = retrieve_space_with_date(
        space.key,
        # make an overlap just in case clocks are off a bit
        updated_after=space.last_import_date - timedelta(minutes=15),
        ignore_labels=ignore_labels,
    )
    updated_pages = [page for page in updated_pages_raw if not isinstance(page, InaccessiblePage)]
    removed_page_ids = [page.page_id for page in updated_pages_raw if isinstance(page, InaccessiblePage)]

    if updated_pages:
        db_pages.upsert_many(space, updated_pages)

    if removed_page_ids:
        db_pages.delete_by_page_ids(removed_page_ids)

    db_spaces.mark_imported(space, import_date)


def __assert_all_pages_accessible(pages_data: list[PageDataDTO | InaccessiblePage]) -> list[PageDataDTO]:
    inaccessible_pages = [page for page in pages_data if isinstance(page, InaccessiblePage)]
    if inaccessible_pages:
        page_ids = [page.page_id for page in inaccessible_pages]
        logging.error("Inacessible pages in space", extra={"page_ids": page_ids})
        raise AssertionError

    return [page for page in pages_data if not isinstance(page, InaccessiblePage)]


def __delete_space_and_related_pages(space: SpaceDTO) -> None:
    logging.info("Deleting space and related pages", extra={"space_key": space.key})
    db_spaces.delete_space_and_related_pages(space.id)


def __remove_non_relevant_pages(space: SpaceDTO, labels: list[str] = confluence_ignore_labels) -> None:
    ignored_by_label_page_ids = set(get_space_page_ids_by_label(space.key, labels))
    all_current_page_ids = set(get_space_page_ids(space.key, status=_PAGE_STATUS_FOR_IMPORT))
    relevant_page_ids = all_current_page_ids - ignored_by_label_page_ids

    db_page_ids = set(db_pages.all_ids_by_space(space))

    non_relevant_page_ids = list(db_page_ids - relevant_page_ids)

    if non_relevant_page_ids:
        logging.info(
            "Deleting Not relevant pages (archived, moved or ignored by label)",
            extra={"space_key": space.key, "page_ids": non_relevant_page_ids},
        )
        db_pages.delete_by_page_ids(non_relevant_page_ids)
