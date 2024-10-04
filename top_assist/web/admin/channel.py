from collections.abc import Sequence

from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette_admin import BaseField, StringField, action
from starlette_admin.contrib.sqla import ModelView

from top_assist.chat_bot.channels import leave_channel
from top_assist.models import ChannelORM
from top_assist.web.admin.mixins import ForbiddenActionsMixin


class ChannelAdmin(ForbiddenActionsMixin, ModelView):
    """Admin view for Slack channels."""

    page_size = 100

    fields: Sequence[BaseField] = [
        StringField("id"),
        StringField("slack_channel_id"),
        StringField("name"),
    ]

    searchable_fields: Sequence[str] = ["slack_user_id"]

    sortable_fields: Sequence[str] = [
        "id",
        "slack_channel_id",
        "name",
    ]

    @action(
        name="leave_channel",
        text="Leave channel",
        confirmation="Are you sure you want to leave this channel?",
        icon_class="fa fa-trash",
        submit_btn_text="Yes, leave channel",
        submit_btn_class="btn-success",
        custom_response=True,
    )
    async def leave_channel_action(self, _request: Request, pks: list[str]):  # noqa: ANN201 (@action has incorrect signature)
        """Remove channel from the list (in-row action)."""
        channel_ids = [int(pk) for pk in pks]

        leave_channel(channel_ids)

        return RedirectResponse("/admin/channels/list", status_code=303)


channel_view = ChannelAdmin(
    ChannelORM,
    label="Slack Channels",
    name="Slack Channels",
    identity="channels",
    icon="fa-regular fa-hashtag",
)
