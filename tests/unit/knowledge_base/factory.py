import itertools
from datetime import UTC, datetime

from top_assist.models.page_data import PageDataDTO

page_id_counter = itertools.count(1)


def create_page_dto(
    *,
    page_id: str | None = None,
    title: str | None = None,
    author: str | None = None,
    content: str | None = None,
    comments: str | None = None,
    space_key: str | None = None,
    created_date: datetime | None = None,
    last_updated: datetime | None = None,
) -> PageDataDTO:
    sequence_id = next(page_id_counter)
    now = datetime.now(UTC)

    return PageDataDTO(
        page_id=page_id or f"{sequence_id}",
        title=title or f"title{sequence_id}",
        author=author or f"author{sequence_id}",
        content=content or f"content{sequence_id}",
        comments=comments or f"comments{sequence_id}",
        space_key=space_key or f"space_key{sequence_id}",
        content_length=len(content or f"content{sequence_id}"),
        created_date=created_date or now,
        last_updated=last_updated or now,
    )
