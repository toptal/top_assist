import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

from atlassian.errors import ApiError, ApiPermissionError  # type: ignore[import-untyped]
from bs4 import BeautifulSoup

from top_assist.configuration import confluence_ignore_labels
from top_assist.models.page_data import PageDataDTO
from top_assist.utils.tracer import ServiceNames, tracer

from ._client import ConfluenceClient as Client


class PageNotFoundError(Exception):  # noqa: D101
    pass


class MissingLabelsError(Exception):  # noqa: D101
    def __init__(self, message: str = "Missing required labels for page retrieval"):
        super().__init__(message)


class InaccessibleSpaceError(Exception):
    """Error raised when a Confluence space cannot be accessed due to permissions or not found."""


@dataclass
class InaccessiblePage:
    """Page that cannot be accessed due to permissions or not found."""

    space_key: str
    page_id: str


@tracer.wrap(service=ServiceNames.confluence.value)
def retrieve_space(
    space_key: str, page_status: str | None = None, ignored_page_ids: set[str] | None = None
) -> list[PageDataDTO | InaccessiblePage]:
    logging.info("Starting space retrieval", extra={"space_key": space_key})

    page_ids = get_space_page_ids(space_key, status=page_status)

    if ignored_page_ids:
        logging.info("Ignoring pages", extra={"page_ids": ignored_page_ids})
        page_ids = list(set(page_ids) - ignored_page_ids)

    pages = __retrieve_pages(space_key, page_ids)
    logging.info("Finished space retrieval", extra={"space_key": space_key})

    return pages


@tracer.wrap(service=ServiceNames.confluence.value)
def retrieve_space_with_date(
    space_key: str, *, updated_after: datetime, ignore_labels: list[str] = confluence_ignore_labels
) -> list[PageDataDTO | InaccessiblePage]:
    log_extra = {"space_key": space_key, "updated_after": updated_after}

    logging.info("Starting space conditional retrieval", extra=log_extra)
    page_ids = __get_space_updated_page_ids(space_key, updated_after, ignore_labels)
    pages = __retrieve_pages(space_key, page_ids)
    logging.info("Finished space conditional retrieval", extra=log_extra)

    return pages


def get_space_page_ids(space_key: str, status: str | None = None) -> list[str]:
    """Retrieves all page IDs in a given space, including child pages.

    Args:
        space_key (str): The key of the Confluence space.
        status (str): The status of the pages to retrieve (current, trashed, draft).

    Returns:
        list[str]: List of page IDs in the space.
    """
    page_ids = []
    start = 0
    limit = 50
    client = Client().confluence
    while True:
        try:
            chunk = client.get_all_pages_from_space(space_key, start=start, limit=limit, status=status)
            start += limit

        except ApiPermissionError as e:
            logging.exception("Permission error", extra={"space_key": space_key})
            raise InaccessibleSpaceError from e

        except Exception:
            logging.exception("Error fetching pages", extra={"space_key": space_key, "limit": limit, "start": start})
            raise

        page_ids.extend([page["id"] for page in chunk])
        if len(chunk) < limit:
            break
    page_ids = list(set(page_ids))
    logging.info("Discovered pages for retrieval", extra={"space_key": space_key, "count": len(page_ids)})

    return page_ids


def get_space_page_ids_by_label(space_key: str, labels: list[str]) -> list[str]:
    """Retrieves all page IDs in a given space, including child pages, that include the specified labels."""
    if not labels:
        raise MissingLabelsError

    cql = f'type=page and space="{space_key}" and label in ({", ".join(labels)})'
    page_ids = __query_page_ids_with_cql(space_key, cql)

    logging.info(
        "Discovered labeled pages",
        extra={"space_key": space_key, "changed_count": len(page_ids), "labels": labels},
    )

    return page_ids


def __get_space_updated_page_ids(
    space_key: str, updated_after: datetime, ignore_labels: list[str] = confluence_ignore_labels
) -> list[str]:
    """Retrieves all page IDs in a given space updated after a certain date."""
    cql = f'type=page and space="{space_key}" and lastModified >= "{updated_after.strftime("%Y-%m-%d %H:%M")}"'

    if ignore_labels:
        cql += f' and label not in ({", ".join(ignore_labels)})'

    changed_page_ids = __query_page_ids_with_cql(space_key, cql)

    logging.info(
        "Discovered pages for retrieval",
        extra={"space_key": space_key, "changed_count": len(changed_page_ids)},
    )

    return changed_page_ids


def __query_page_ids_with_cql(space_key: str, cql: str) -> list[str]:
    page_ids = []
    limit = 50

    client = Client()
    for chunk in client.cql_paginated_fetcher(cql, limit=limit):
        logging.debug("Fetched pages chunk with CQL", extra={"space_key": space_key, "limit": limit, "cql": cql})

        page_ids.extend([page["content"]["id"] for page in chunk])

    return page_ids


def __strip_html_tags(content: str) -> str:
    soup = BeautifulSoup(content, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def __get_page_comments_content(page_id: str) -> str:
    result = []
    start = 0
    limit = 25
    client = Client().confluence
    while True:
        try:
            chunk = client.get_page_comments(
                page_id,
                depth="all",
                start=start,
                limit=limit,
                expand="body.storage",
            )["results"]
        except Exception:
            logging.exception(
                "Error fetching page comments",
                extra={"page_id": page_id, "limit": limit, "start": start},
            )
            raise

        for comment in chunk:
            content = comment["body"]["storage"]["value"]
            content = __strip_html_tags(content)
            result.append(content)

        start += limit
        if len(chunk) < limit:
            break

    return "\n".join(result)


def __is_inaccessible_page_error(e: Exception) -> bool:
    return (
        isinstance(e, ApiError)
        and isinstance(e.reason, Exception)
        and len(e.reason.args) > 0
        and isinstance(e.reason.args[0], str)
        and e.reason.args[0].startswith("com.atlassian.confluence.api.service.exceptions.NotFoundException")
    )


def __retrieve_page(page_id: str, space_key: str) -> PageDataDTO | InaccessiblePage:
    try:
        page = Client().confluence.get_page_by_id(page_id, expand="body.storage,history,version")

    except Exception as e:
        if __is_inaccessible_page_error(e):
            return InaccessiblePage(space_key=space_key, page_id=page_id)

        logging.exception(
            "Error retrieving page",
            extra={"page_id": page_id, "space_key": space_key},
        )
        raise

    if not page:
        logging.error("Page not found", extra={"page_id": page_id, "space_key": space_key})
        raise PageNotFoundError

    logging.debug("Processing page...", extra={"page_id": page_id, "space_key": space_key})
    page_title = __strip_html_tags(page["title"])
    page_author = page["history"]["createdBy"]["displayName"]
    created_date = page["history"]["createdDate"]
    last_updated = page["version"]["when"]
    page_content = __strip_html_tags(page.get("body", {}).get("storage", {}).get("value", ""))
    page_comments_content = __get_page_comments_content(page_id)

    page_data = PageDataDTO(
        space_key=space_key,
        page_id=page_id,
        title=page_title,
        author=page_author,
        content=page_content,
        comments=page_comments_content,
        created_date=__parse_datetime(created_date),
        last_updated=__parse_datetime(last_updated),
        content_length=len(page_content),
    )

    logging.info("Page retrieved", extra={"space_key": space_key, "page_id": page_id})
    return page_data


def __retrieve_pages(space_key: str, page_ids: list[str]) -> list[PageDataDTO | InaccessiblePage]:
    def worker(page_id: str) -> PageDataDTO | InaccessiblePage:
        return __retrieve_page(page_id, space_key)

    with ThreadPoolExecutor(max_workers=10) as executor:
        pages = executor.map(worker, page_ids)
        return list(pages)


def __parse_datetime(date_str: str) -> datetime:
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
