from urllib.parse import quote

from top_assist.auth.sign_in_flow import (
    generate_provider_oauth_link,
)
from top_assist.configuration import confluence_oauth_client_id


def test_generate_provider_oauth_link() -> None:
    # When
    result = generate_provider_oauth_link(state="test_state")

    # Then
    assert result == "".join([
        "https://auth.atlassian.com/authorize?",
        "&".join([
            "audience=api.atlassian.com",
            f"client_id={confluence_oauth_client_id}",
            f"scope={quote("search:confluence offline_access read:me")}",
            "redirect_uri=http://localhost:8080/confluence/oauth/callback",
            "state=test_state",
            "response_type=code",
            "prompt=consent",
        ]),
    ])
