from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Form, Response
from fastapi.responses import RedirectResponse

from top_assist.chat_bot.channels import update_channels
from top_assist.knowledge_base.importer import import_confluence_space, pull_updates

router = APIRouter()

# Note that all the routes here will have the /admin prefix as we are mounting them in admin/__init__.py


@router.post("/import_space/{space_key}/{space_name}")
async def process_import_space(space_key: str, space_name: str, background_tasks: BackgroundTasks) -> Response:
    background_tasks.add_task(import_confluence_space, space_key=space_key, space_name=space_name)

    return RedirectResponse("/admin/spaces/list", status_code=303)


@router.post("/import_spaces")
async def process_import_spaces(
    background_tasks: BackgroundTasks, selected_spaces: Annotated[list[str], Form()]
) -> Response:
    spaces = {space.split("__")[0]: space.split("__")[1] for space in selected_spaces}

    for key, name in spaces.items():
        background_tasks.add_task(import_confluence_space, space_key=key, space_name=name)

    return RedirectResponse("/admin/spaces/list", status_code=303)


@router.post("/update_spaces")
async def process_update_spaces(background_tasks: BackgroundTasks) -> Response:
    background_tasks.add_task(pull_updates)

    return RedirectResponse("/admin/spaces/list", status_code=303)


@router.post("/update_channels")
async def process_update_channels(background_tasks: BackgroundTasks) -> Response:
    background_tasks.add_task(update_channels)

    return RedirectResponse("/admin/channels/list", status_code=303)


@router.get("/test")
def test() -> dict[str, str]:
    return {"message": "It's working"}
