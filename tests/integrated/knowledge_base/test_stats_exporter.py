from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

import top_assist.database.spaces as db_spaces
from top_assist.database.database import Session
from top_assist.knowledge_base.stats_exporter import export_spaces_stats
from top_assist.models.page_data import PageDataORM
from top_assist.models.space import SpaceDTO, SpaceORM

_SPACES_ID_DB = 2
_FIRST_SPACE_KEY = "first_space_key"
_SECOND_SPACE_KEY = "second_space_key"


def __generate_page(space: SpaceDTO, page_id: str) -> PageDataORM:
    new_page = PageDataORM(
        page_id=page_id,
        space_key=space.key,
        space_id=space.id,
        title=f"Page #{page_id}",
        author="test author",
        created_date=datetime.now(),  # noqa: DTZ005
        last_updated=datetime.now(),  # noqa: DTZ005
        content="content",
        comments="comments",
    )
    return new_page


@pytest.fixture()
def _setup_db(db_session: Session) -> None:
    db_session.begin()
    space1 = db_spaces.find_or_create(space_key=_FIRST_SPACE_KEY, space_name="first_space_name")
    space2 = db_spaces.find_or_create(space_key=_SECOND_SPACE_KEY, space_name="second_space_name")

    page_1 = __generate_page(space1, "1")
    page_2 = __generate_page(space1, "2")
    page_3 = __generate_page(space2, "3")

    db_session.add_all([page_1, page_2, page_3])


@pytest.mark.usefixtures("_setup_db")
@patch("top_assist.knowledge_base.stats_exporter.update_page_in_confluence", autospec=True)
@patch("top_assist.knowledge_base.stats_exporter.db_spaces.find_or_create", autospec=True)
@patch("top_assist.knowledge_base.stats_exporter.update_space_in_db", autospec=True)
def test_export_spaces_stats(
    mock_update_space_in_db: MagicMock,
    mock_find_or_create: MagicMock,
    mock_update_page_in_confluence: MagicMock,
    db_session: Session,
) -> None:
    assert db_session.query(SpaceORM).count() == _SPACES_ID_DB
    assert db_session.query(PageDataORM).count() == 3

    export_spaces_stats()

    args, kwargs = mock_update_page_in_confluence.call_args

    expected_content = """
            <tr>
                <td><p style="text-align: center;">first_space_key</p></td>
                <td><p style="text-align: center;">first_space_name</p></td>
                <td><p style="text-align: center;">2</p></td>
            </tr>
            <tr>
                <td><p style="text-align: center;">second_space_key</p></td>
                <td><p style="text-align: center;">second_space_name</p></td>
                <td><p style="text-align: center;">1</p></td>
            </tr>
        """

    assert expected_content in kwargs["content"]

    mock_update_page_in_confluence.assert_called_once()
    mock_find_or_create.assert_called_once()
    mock_update_space_in_db.assert_called_once()
