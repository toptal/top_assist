from datetime import datetime

import pytest

import top_assist.database.spaces as db_spaces
from top_assist.database.database import Session
from top_assist.models import PageDataORM

CONTENT = "My content"
NEW_CONTENT = "New content foó"


@pytest.fixture()
def _setup_db(db_session: Session) -> None:
    db_session.begin()
    space_key = "my_space_key"

    space = db_spaces.find_or_create(space_key=space_key, space_name="my_space_name")

    new_page = PageDataORM(
        page_id=111,
        space_key=space_key,
        space_id=space.id,
        title="test",
        author="test author",
        created_date=datetime.now(),  # noqa: DTZ005
        last_updated=datetime.now(),  # noqa: DTZ005
        content=CONTENT,
        comments="comments",
    )
    db_session.add(new_page)


@pytest.mark.usefixtures("_setup_db")
def test_content_length_change(db_session: Session) -> None:
    # Given
    assert db_session.query(PageDataORM).count() == 1
    page = db_session.query(PageDataORM).first()
    assert page is not None, "Page should not be None"
    assert page.content == CONTENT
    assert page.content_length == len(CONTENT.encode())

    # When
    page.content = NEW_CONTENT

    # Then
    updated_page = db_session.query(PageDataORM).first()
    assert updated_page is not None, "Page should not be None"
    assert updated_page.content == NEW_CONTENT
    assert updated_page.content_length == len(NEW_CONTENT.encode())
