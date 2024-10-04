from sqlalchemy import asc, func
from starlette_admin.views import CustomView, Jinja2Templates, Request, Response

import top_assist.database.pages as db_pages
import top_assist.database.spaces as db_spaces
from top_assist.confluence.spaces import ConfluenceSpaceInfo, retrieve_space_list
from top_assist.database.database import get_db_session
from top_assist.models import PageDataORM, SpaceORM, UserAuthORM
from top_assist.models.space import SpaceDTO


class HomeAdmin(CustomView):
    """Admin view for the home page."""

    async def render(self, request: Request, templates: Jinja2Templates) -> Response:
        with get_db_session() as session:
            space_count = session.query(func.count(SpaceORM.id)).scalar()
            pages_count = session.query(func.count(PageDataORM.id)).scalar()
            users_count = session.query(func.count(UserAuthORM.id)).scalar()

            pages_in_vector_db = db_pages.count_embeddings()
            space = session.query(SpaceORM).order_by(asc(SpaceORM.last_import_date)).first()
            old_space = SpaceDTO.from_orm(space) if space else None

            spaces_available_for_import = self.spaces_available_for_import()

        return templates.TemplateResponse(
            request=request,
            name="report.html",
            context={
                "old_space_name": old_space.name if old_space else None,
                "old_space_key": old_space.key if old_space else None,
                "old_space_last_import_date": old_space.last_import_date if old_space else None,
                "space_count": space_count,
                "pages_count": pages_count,
                "users_count": users_count,
                "pages_in_vector_db": pages_in_vector_db,
                "spaces_available_for_import": spaces_available_for_import,
            },
        )

    @staticmethod
    def spaces_available_for_import() -> list[ConfluenceSpaceInfo]:
        """Get list of spaces available for import from Confluence not yet imported to the database."""
        imported_space_keys = {space.key for space in db_spaces.all_spaces()}
        confluence_spaces = retrieve_space_list()
        available_for_import = [space for space in confluence_spaces if space.key not in imported_space_keys]

        return available_for_import
