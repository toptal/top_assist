from starlette.requests import Request


class ForbiddenActionsMixin:
    """Disable default actions for the admin view."""

    def can_create(self, _request: Request) -> bool:
        return False

    def can_edit(self, _request: Request) -> bool:
        return False

    def can_delete(self, _request: Request) -> bool:
        return False
