from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from freezegun import freeze_time

import top_assist.database.spaces as db_spaces
from top_assist.confluence.spaces import ConfluenceClient
from top_assist.database.database import Session
from top_assist.knowledge_base.importer import pull_updates
from top_assist.models.page_data import PageDataDTO, PageDataORM
from top_assist.models.space import SpaceORM

_SPACES_ID_DB = 2
_NORMAL_SPACE_KEY = "space_key"
_ARCHIVED_SPACE_KEY = "archived_space_key"
_UPDATED_PAGE_ID = "123"
_REMOVED_PAGE_ID = "529"


@freeze_time("2012-01-14")
@pytest.fixture()
def _setup_db(db_session: Session) -> None:
    db_session.begin()
    space = db_spaces.find_or_create(space_key=_NORMAL_SPACE_KEY, space_name="space_name")
    space_archived = db_spaces.find_or_create(space_key=_ARCHIVED_SPACE_KEY, space_name="archived_space_name")

    new_page = PageDataORM(
        page_id=_REMOVED_PAGE_ID,
        space_key=_NORMAL_SPACE_KEY,
        space_id=space.id,
        title="test",
        author="test author",
        created_date=datetime.now(),  # noqa: DTZ005
        last_updated=datetime.now(),  # noqa: DTZ005
        content="content",
        comments="comments",
    )
    db_session.add(new_page)
    db_spaces.mark_imported(space, import_date=datetime.now(UTC) - timedelta(days=1))
    db_spaces.mark_imported(space_archived, import_date=datetime.now(UTC) - timedelta(days=1))


@pytest.fixture()
def _patch_vector_db() -> Generator:
    with (
        patch("top_assist.database.pages.vector_pages.import_data", autospec=True),
        patch("top_assist.database._vector.engine.embed_text", autospec=True, return_value=[0.0, 1.0]),
        patch("top_assist.database.pages.vector_pages.delete_embeddings", autospec=True),
    ):
        yield


def client_retrieve_space_list_side_effect(status: str) -> list[dict[str, str]]:
    if status == "archived":
        return [{"key": _ARCHIVED_SPACE_KEY, "name": "archived_space_name", "status": "archived"}]

    return [{"key": _NORMAL_SPACE_KEY, "name": "space_name", "status": "current"}]


def client_retrieve_pages_side_effect(space_key: str, page_ids: list[str]) -> list[PageDataDTO]:  # noqa: ARG001
    if space_key == _NORMAL_SPACE_KEY:
        return [
            PageDataDTO(
                page_id=_UPDATED_PAGE_ID,
                space_key=_NORMAL_SPACE_KEY,
                title="title",
                author="author",
                content="content",
                comments="comments",
                created_date=datetime.now(UTC),
                last_updated=datetime.now(UTC),
                content_length=len("content"),
            )
        ]

    return []


@freeze_time("2012-01-14")
@pytest.mark.usefixtures("_setup_db", "_patch_vector_db")
@patch("top_assist.confluence.spaces.ConfluenceClient", autospec=True)
@patch("top_assist.knowledge_base.importer.get_space_page_ids", autospec=True)
@patch("top_assist.knowledge_base.importer.get_space_page_ids_by_label", autospec=True)
@patch("top_assist.confluence.retriever.__get_space_updated_page_ids", autospec=True)
@patch("top_assist.confluence.retriever.__retrieve_pages", autospec=True)
def test_pull_updates(
    mock_retrieve_pages: MagicMock,
    mock_get_space_updated_page_ids: MagicMock,
    mock_get_space_page_ids_by_label: MagicMock,
    mock_get_space_page_ids: MagicMock,
    mock_confluence_client_class: MagicMock,
    db_session: Session,
) -> None:
    current_time = datetime.now(tz=UTC)

    mock_confluence_client = create_autospec(ConfluenceClient)
    mock_confluence_client.retrieve_space_list.side_effect = client_retrieve_space_list_side_effect
    mock_confluence_client_class.return_value = mock_confluence_client
    mock_get_space_page_ids.side_effect = [[_UPDATED_PAGE_ID, "124"], ["321", "322"]]
    mock_get_space_page_ids_by_label.side_effect = [["125"], []]
    mock_get_space_updated_page_ids.side_effect = [[_UPDATED_PAGE_ID], ["321"]]
    mock_retrieve_pages.side_effect = client_retrieve_pages_side_effect

    assert db_session.query(SpaceORM).count() == _SPACES_ID_DB
    assert db_session.query(PageDataORM).count() == 1

    pull_updates()

    assert db_session.query(SpaceORM).count() == 1
    assert db_session.query(PageDataORM).count() == 1
    updated_space = db_session.query(SpaceORM).first()

    assert updated_space is not None
    assert updated_space.last_import_date == current_time

    updated_page = db_session.query(PageDataORM).filter_by(space_id=updated_space.id).first()

    assert updated_page is not None

    assert updated_page.page_id == _UPDATED_PAGE_ID
