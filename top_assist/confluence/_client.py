import logging
import time
import typing
from collections.abc import Generator

from atlassian import Confluence
from requests import Session

from top_assist.configuration import confluence_api_token, confluence_base_url, confluence_cloud_id, confluence_username


class InvalidAccessTokenError(Exception):
    pass


class ConfluenceClient:
    """A class to handle interactions with the Confluence API."""

    @classmethod
    def with_access_token(cls, access_token: str) -> typing.Self:
        if not access_token:
            raise InvalidAccessTokenError

        session = Session()
        session.headers["Authorization"] = f"Bearer {access_token}"

        sdk_client = Confluence(url=f"https://api.atlassian.com/ex/confluence/{confluence_cloud_id}/", session=session)

        return cls(sdk_client)

    def __init__(self, sdk_client: Confluence = None):
        """Initialize the Confluence client.

        Args:
        sdk_client (atlassian.Confluence): An existing Confluence SDK client (optional).
        """
        if sdk_client:
            self.confluence = sdk_client
        else:
            self.confluence = Confluence(
                url=confluence_base_url,
                username=confluence_username,
                password=confluence_api_token,
            )

    def page_exists(self, space_key: str, title: str) -> bool:
        """Check if a page with the given title exists in the given space."""
        return self.confluence.page_exists(space_key, title)

    def get_page_id_by_title(self, space_key: str, title: str) -> str:
        """Retrieve the page ID for a given page title in a given space."""
        try:
            return self.confluence.get_page_id(space_key, title)
        except Exception:
            logging.exception("Error retrieving page ID", extra={"space_key": space_key, "title": title})
            raise

    def update_page(self, page_id: str, title: str, content: str, *, minor_edit: bool) -> dict:
        """Update an existing page with new content."""
        try:
            response = self.confluence.update_page(page_id=page_id, title=title, body=content, minor_edit=minor_edit)
            logging.info("Page updated successfully", extra={"page_id": page_id, "title": title})
            return response
        except Exception:
            logging.exception("Error updating page", extra={"page_id": page_id, "title": title})
            raise

    def retrieve_space_list(self, status: str = "current") -> list[dict]:
        """Retrieve a complete list of available spaces in Confluence using pagination.

        Returns:
            list: A comprehensive list of space data objects.
        """
        all_spaces = []
        start = 0
        limit = 300  # default limit is 500

        while True:
            response = self.confluence.get_all_spaces(
                start=start,
                limit=limit,
                space_status=status,  # exclude archived spaces by default
            )
            spaces = response.get("results", [])
            if not spaces:
                break

            all_spaces.extend(spaces)
            start += len(spaces)

        return all_spaces

    def cql_paginated_fetcher(self, cql: str, *, limit: int) -> Generator[list, None, None]:
        next_path = None
        while True:
            try:
                response = self.confluence.cql(cql, limit=limit) if not next_path else self.confluence.get(next_path)
                chunk = response["results"]
                next_path = response["_links"].get("next")

                logging.debug(
                    "Fetched pages chunk with CQL",
                    extra={"cql": cql, "limit": limit, "next_path": next_path},
                )

                yield chunk

            except Exception:
                logging.exception(
                    "Error fetching pages with CQL",
                    extra={"cql": cql, "limit": limit, "next_path": next_path},
                )
                raise

            if not next_path:
                break

    def cql_search(self, cql: str) -> list:
        try:
            response = self.confluence.cql(cql)
            results = response["results"]
            logging.debug("CQL search results", extra={"cql": cql, "results": results})
            return results
        except Exception:
            logging.exception("Error executing CQL search", extra={"cql": cql})
            raise

    @staticmethod
    def generate_space_key(space_name: str) -> str:
        # Create a base space key by taking the first two letters of each word
        base_key = "".join(word[:2].upper() for word in space_name.split())
        # Append a timestamp to the base key
        timestamp = int(time.time())
        return f"{base_key}{timestamp}"
