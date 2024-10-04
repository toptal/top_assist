from collections.abc import Sequence
from typing import TYPE_CHECKING

from starlette.requests import Request
from starlette_admin import BaseField, DateTimeField, HasOne, NumberField, StringField
from starlette_admin.actions import link_row_action
from starlette_admin.contrib.sqla import ModelView

from top_assist.configuration import confluence_base_url
from top_assist.models import PageDataORM
from top_assist.web.admin.mixins import ForbiddenActionsMixin

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class PageDataAdmin(ForbiddenActionsMixin, ModelView):
    """Page Data admin view."""

    page_size = 100

    fields: Sequence[BaseField] = [
        StringField("id"),
        StringField("page_id"),
        StringField("space_key"),
        StringField("title"),
        StringField("author"),
        StringField("space_id"),
        NumberField("content_length"),
        StringField("content", exclude_from_list=True),
        StringField("comments", exclude_from_list=True),
        DateTimeField("created_date"),
        DateTimeField("last_updated"),
        HasOne("space", identity="spaces"),
    ]

    searchable_fields: Sequence[str] = ["page_id", "space_key", "author", "content_length"]

    sortable_fields: Sequence[str] = [
        "id",
        "page_id",
        "space_key",
        "author",
        "space_id",
        "created_date",
        "last_updated",
        "content_length",
    ]

    @link_row_action(
        name="see_in_confluence",
        text="See in Confluence",
        icon_class="fas fa-arrow-up-right-from-square",
    )
    def go_to_example_row_action(self, request: Request, pk: str) -> str:
        """Generate URL link to the page in Confluence."""
        session: Session = request.state.session
        obj = session.get(self.model, pk)
        page_id = getattr(obj, "page_id", None)
        space = getattr(obj, "space_key", None)

        return f"https://{confluence_base_url}/wiki/spaces/{space}/pages/{page_id}"


page_data_view = PageDataAdmin(
    PageDataORM,
    label="Pages",
    name="Pages",
    identity="pages",
    icon="fa-regular fa-file-lines",
)
