import requests
from pydantic import BaseModel

from top_assist.configuration import (
    confluence_oauth_authorization_url_template,
    confluence_oauth_client_id,
    confluence_oauth_client_secret,
    confluence_oauth_redirect_uri,
)

_ATLASSIAN_TOKEN_URL = "https://auth.atlassian.com/oauth/token"  # noqa: S105


class ConfluenceOAuthTokens(BaseModel):  # noqa: D101
    access_token: str
    refresh_token: str
    expires_in: int


def generate_confluence_oauth_link(*, state: str) -> str:
    return confluence_oauth_authorization_url_template.format(
        state=state,
        client_id=confluence_oauth_client_id,
        callback_url=confluence_oauth_redirect_uri,
    )


def tokens_from_oauth_code(code: str) -> ConfluenceOAuthTokens:
    return __retrieve_tokens({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": confluence_oauth_redirect_uri,
        "client_id": confluence_oauth_client_id,
        "client_secret": confluence_oauth_client_secret,
    })


def tokens_with_refresh_token(refresh_token: str) -> ConfluenceOAuthTokens:
    return __retrieve_tokens({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": confluence_oauth_client_id,
        "client_secret": confluence_oauth_client_secret,
    })


def __retrieve_tokens(data: dict[str, str]) -> ConfluenceOAuthTokens:
    response = requests.post(_ATLASSIAN_TOKEN_URL, data=data, timeout=10)
    response.raise_for_status()
    return ConfluenceOAuthTokens.model_validate_json(response.text)
