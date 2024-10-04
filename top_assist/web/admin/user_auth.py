from collections.abc import Sequence

from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette_admin import BaseField, DateTimeField, StringField, action, row_action
from starlette_admin.contrib.sqla import ModelView

from top_assist.database import user_auth as db_user_auth
from top_assist.models import UserAuthORM
from top_assist.web.admin.mixins import ForbiddenActionsMixin


class UserAuthAdmin(ForbiddenActionsMixin, ModelView):
    """Admin view for user authentications."""

    page_size = 100

    fields: Sequence[BaseField] = [
        StringField("id"),
        StringField("slack_user_id"),
        DateTimeField("access_token_expires_at"),
        DateTimeField("created_at"),
        DateTimeField("updated_at"),
    ]

    searchable_fields: Sequence[str] = ["slack_user_id"]

    sortable_fields: Sequence[str] = [
        "id",
        "slack_user_id",
        "access_token_expires_at",
    ]

    @row_action(
        name="cleanup_credentials",
        text="Cleanup User credentials",
        confirmation="Are you sure you want to delete the credentials for the selected user?",
        icon_class="fa fa-refresh",
        submit_btn_text="Delete",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
    )
    async def delete_credentials_action(self, _request: Request, pk: str) -> str:
        """Delete user credentials."""
        db_user_auth.delete_by_id(int(pk))

        return "Credentials were successfully removed from user"

    @action(
        name="cleanup_multiple_credentials",
        text="Cleanup Users Credentials",
        confirmation="Are you sure you want to delete the credentials for the selected users?",
        icon_class="fa fa-refresh",
        submit_btn_text="Yes, delete credentials for the selected users",
        submit_btn_class="btn-success",
        custom_response=True,
    )
    async def delete_multiple_credentials_action(self, _request: Request, pks: list[str]):  # noqa: ANN201 (@action has incorrect signature)
        """Delete multiple user credentials."""
        user_auth_ids = [int(pk) for pk in pks]
        for user_auth_id in user_auth_ids:
            db_user_auth.delete_by_id(user_auth_id)

        return RedirectResponse("/admin/user_auth/list", status_code=303)


user_auth_view = UserAuthAdmin(
    UserAuthORM,
    label="Users Auth",
    name="UsersAuth",
    identity="user_auth",
    icon="fa-regular fa-users",
)
