import logging
from dataclasses import dataclass

import requests
from pydantic import BaseModel, EmailStr


class FetchingConfluenceEmailError(Exception):  # noqa: D101
    pass


class FetchingConfluenceEmailStatusCodeError(FetchingConfluenceEmailError):  # noqa: D101
    def __init__(self, status_code: int):
        super().__init__(f"Failed to fetch confluence email: status_code {status_code}")


@dataclass
class ConfluenceUserEmail:  # noqa: D101
    email: str
    is_email_verified: bool


def fetch_confluence_email(*, user_access_token: str) -> ConfluenceUserEmail:
    try:
        response = requests.get(
            _ATLASSIAN_ME_URL,
            headers={
                "Authorization": f"Bearer {user_access_token}",
                "Accept": "application/json",
            },
            timeout=10,
        )

        response.raise_for_status()
        me = _MeResponse.model_validate_json(response.text)
    except Exception as e:
        logging.exception("Failed to parse email response", extra={"response": response.text, "error": e})
        raise FetchingConfluenceEmailError from e

    return ConfluenceUserEmail(email=me.email, is_email_verified=me.email_verified)


_ATLASSIAN_ME_URL = "https://api.atlassian.com/me"


class _MeResponse(BaseModel):
    email: EmailStr
    email_verified: bool
