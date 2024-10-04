from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin import DropDown
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from starlette_admin.contrib.sqla import Admin
from starlette_admin.exceptions import LoginFailed
from starlette_admin.views import Link

from top_assist.configuration import admin_extra_links, admin_password, admin_session_secret_key, admin_user
from top_assist.database.database import engine
from top_assist.web.admin.channel import channel_view
from top_assist.web.admin.home import HomeAdmin
from top_assist.web.admin.page_data import page_data_view
from top_assist.web.admin.qa_interaction import qa_interaction_view
from top_assist.web.admin.router import router as admin_router
from top_assist.web.admin.space import space_view
from top_assist.web.admin.user_auth import user_auth_view

users = {admin_user: {"name": "Admin"}}


class UsernameAndPasswordProvider(AuthProvider):
    """Username and password authentication provider."""

    async def login(  # noqa: PLR0913
        self,
        username: str,
        password: str,
        remember_me: bool,  # noqa: FBT001
        request: Request,
        response: Response,
    ) -> Response:
        """Custom login method to validate user credentials."""
        if username == admin_user and password == admin_password:
            expires_at = (
                datetime.now(UTC) + timedelta(days=1) if remember_me else datetime.now(UTC) + timedelta(minutes=10)
            )
            request.session.update({"username": username, "expires_at": expires_at.isoformat()})
            return response

        raise LoginFailed("Invalid username or password")  # noqa: TRY003

    async def is_authenticated(self, request: Request) -> bool:
        username = request.session.get("username", None)
        expires_at = request.session.get("expires_at", None)

        if username in users and expires_at and datetime.now(UTC) < datetime.fromisoformat(expires_at):
            """
            Save current `user` object in the request state. Can be used later
            to restrict access to connected user.
            """
            request.state.user = users.get(request.session["username"])
            return True

        return False

    def get_admin_config(self, request: Request) -> AdminConfig:
        """Customize admin panel according to current_user."""
        user = request.state.user  # Retrieve current user
        # Update app title according to current_user
        custom_app_title = "Hello, " + user["name"] + "!"
        # Update logo url according to current_user
        return AdminConfig(
            app_title=custom_app_title,
        )

    def get_admin_user(self, request: Request) -> AdminUser:
        user = request.state.user  # Retrieve current user
        return AdminUser(username=user["name"])

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response


def setup_admin_panel(app: FastAPI) -> None:
    admin = Admin(
        engine,
        title="Top Assist",
        index_view=HomeAdmin(label="Home", icon="fa fa-home"),
        templates_dir="top_assist/web/admin/templates",
        auth_provider=UsernameAndPasswordProvider(),
        middlewares=[Middleware(SessionMiddleware, secret_key=admin_session_secret_key)],
    )

    admin.add_view(page_data_view)
    admin.add_view(space_view)
    admin.add_view(user_auth_view)
    admin.add_view(qa_interaction_view)
    admin.add_view(channel_view)

    link_views = []

    for link in admin_extra_links:
        link_views.extend([Link(link["name"], url=link["url"], target="_blank")])

    admin.add_view(DropDown("Links", icon="fa fa-link", views=list(link_views)))
    admin.routes.extend(admin_router.routes)  # type: ignore [arg-type] # there is some mismatch between route types between FastAPI and Starlette
    admin.mount_to(app)
