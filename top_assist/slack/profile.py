from dataclasses import dataclass

from ._client import WebClient


class FetchingSlackEmailError(Exception):  # noqa: D101
    pass


@dataclass
class SlackUserEmail:  # noqa: D101
    email: str
    is_email_confirmed: bool


def fetch_slack_email(*, slack_user_id: str) -> SlackUserEmail:
    try:
        user = WebClient.default().fetch_user_info(slack_user_id=slack_user_id)
    except Exception as e:
        raise FetchingSlackEmailError from e

    return SlackUserEmail(email=user.profile.email, is_email_confirmed=user.is_email_confirmed)
