from collections.abc import Sequence

from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette_admin import BaseField, DateTimeField, StringField, action, row_action
from starlette_admin.contrib.sqla import ModelView

import top_assist.database.spaces as db_spaces
from top_assist.models import SpaceORM
from top_assist.web.admin.mixins import ForbiddenActionsMixin


class PagesCounterField(StringField):
    """Custom field to display number of pages in the space through relationship."""

    async def parse_obj(self, _request: Request, obj: SpaceORM) -> int:
        """Return number of pages in the space."""
        return len(obj.pages)


delete_space = db_spaces.delete_space_and_related_pages


class SpaceAdmin(ForbiddenActionsMixin, ModelView):
    """Admin view for Confluence spaces."""

    page_size = 100

    fields: Sequence[BaseField] = [
        StringField("id"),
        StringField("space_key"),
        StringField("space_name"),
        PagesCounterField("pages_counter", label="Number of Pages"),
        DateTimeField("last_import_date"),
    ]

    searchable_fields: Sequence[str] = ["space_key", "space_name"]

    sortable_fields: Sequence[str] = ["id", "space_key", "space_name", "page_count", "last_import_date"]

    row_actions: Sequence[str] = ["view", "delete_space"]

    @row_action(
        name="delete_space",
        text="Delete space with pages",
        confirmation="Are you sure you want to delete selected space?",
        icon_class="fa fa-trash",
        submit_btn_text="Delete",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
    )
    async def delete_with_pages_action(self, _request: Request, pk: str) -> str:
        """Delete space with its pages."""
        affected_pages = delete_space(int(pk))

        return f"{affected_pages.removed_count} pages were successfully deleted for the space"

    @action(
        name="delete_spaces",
        text="Delete spaces with pages",
        confirmation="Are you sure you want to delete selected items?",
        icon_class="fa fa-trash",
        submit_btn_text="Yes, delete all",
        submit_btn_class="btn-success",
        custom_response=True,
    )
    async def delete_spaces_with_pages_action(self, _request: Request, pks: list[str]):  # noqa: ANN201 (@action has incorrect signature)
        """Delete multiple spaces with their pages."""
        space_ids = [int(pk) for pk in pks]
        for space_id in space_ids:
            delete_space(space_id)

        return RedirectResponse("/admin/spaces/list", status_code=303)


space_view = SpaceAdmin(
    SpaceORM,
    label="Spaces",
    name="Spaces",
    identity="spaces",
    icon="fa-regular fa-copy",
)
