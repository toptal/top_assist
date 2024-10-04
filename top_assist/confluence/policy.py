import logging

import requests

from ._client import ConfluenceClient


class InvalidAuthError(Exception):  # noqa: D101
    def __init__(self, slack_user_id: str):
        super().__init__(f"Invalid Auth for {slack_user_id}")


class PageAccessPolicy:
    """Policy for checking access to Confluence pages."""

    def __init__(self, *, slack_user_id: str, confluence_access_token: str) -> None:
        self.slack_user_id = slack_user_id
        self.confluence_access_token = confluence_access_token

    def accessible_pages(self, page_ids: list[str]) -> set[str]:
        return accessible_page_ids(
            page_ids,
            slack_user_id=self.slack_user_id,
            user_confluence_access_token=self.confluence_access_token,
        )


def accessible_page_ids(page_ids: list[str], *, slack_user_id: str, user_confluence_access_token: str) -> set[str]:
    """Filter out pages that the user does not have access to.

    Args:
        page_ids: List of page IDs to check access for.
        slack_user_id: Slack user ID.
        user_confluence_access_token: User's Confluence access token.

    Returns:
        set[str]: Set of page IDs that the user has access to.
    """
    if not page_ids:
        return set()

    client = ConfluenceClient.with_access_token(user_confluence_access_token)
    cql_query = f"id in ({",".join(page_ids)})"

    try:
        results = client.cql_search(cql=cql_query)
        allowed_page_ids = {page["content"]["id"] for page in results}  # Use set for faster lookups
        logging.debug(
            "Pages filtered by access", extra={"slack_user_id": slack_user_id, "allowed_page_ids": allowed_page_ids}
        )

        return allowed_page_ids
    except requests.HTTPError as e:
        if e.response.status_code in {requests.codes.unauthorized, requests.codes.forbidden}:
            raise InvalidAuthError(slack_user_id) from e

        logging.exception(
            "HTTP error checking page access",
            extra={"slack_user_id": slack_user_id, "page_ids": page_ids, "status_code": e.response.status_code},
        )
        raise
    except Exception:
        logging.exception("Error checking page access", extra={"slack_user_id": slack_user_id, "page_ids": page_ids})
        raise
