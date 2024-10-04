import typing
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy.orm import validates
from starlette.requests import Request

from top_assist.configuration import confluence_base_url

from .base import (
    Base,
    ForeignKey,
    Index,
    Integer,
    Mapped,
    int_pk,
    mapped_column,
    relationship,
    timestamp,
    unique_string,
)

if TYPE_CHECKING:
    from .space import SpaceORM


class PageDataORM(Base):
    """SQLAlchemy model for storing Confluence page data.

    Attr:
        id: The primary key of the page.
        page_id: The primary key of the page.
        space_key: Confluence space key.
        title: Page title.
        author: Author of the page.
        space_id: The primary key of the space.
        created_date: The timestamp when the page was created in Confluence.
        last_updated: The timestamp of the last update in Confluence.
        content: Page content.
        comments: Page comments.
        content_length: The length of the page content in bytes.
    """

    __tablename__ = "page_data"

    id: Mapped[int_pk]
    page_id: Mapped[unique_string]
    space_key: Mapped[str]
    title: Mapped[str]
    author: Mapped[str]
    space_id: Mapped[int] = mapped_column(ForeignKey("spaces.id"))
    created_date: Mapped[timestamp]
    last_updated: Mapped[timestamp]
    content: Mapped[str]
    comments: Mapped[str]
    content_length: Mapped[int] = mapped_column(Integer, default=0)

    space: Mapped["SpaceORM"] = relationship(back_populates="pages")

    repr_cols_num = 3

    __table_args__ = (Index("ix_page_data_page_id", "page_id"),)

    @validates("content")
    def update_content_length(self, _request: Request, value: str) -> str:
        self.content_length = len(value.encode()) if value else 0
        return value


class PageDataDTO(BaseModel):
    """Data transfer object for PageDataORM.

    Attr:
        page_id: The primary key of the page.
        space_key: Confluence space key.
        title: Page title.
        author: Author of the page.
        content: Page content.
        comments: Page comments.
        created_date: The timestamp when the page was created in Confluence.
        last_updated: The timestamp of the last update in Confluence.
        content_length: The length of the page content in bytes.
    """

    page_id: str
    space_key: str
    title: str
    author: str
    content: str
    comments: str
    created_date: datetime
    last_updated: datetime
    content_length: int

    @classmethod
    def from_orm(cls, model: PageDataORM) -> typing.Self:
        return cls(
            page_id=model.page_id,
            space_key=model.space_key,
            title=model.title,
            author=model.author,
            content=model.content,
            comments=model.comments,
            created_date=model.created_date,
            last_updated=model.last_updated,
            content_length=model.content_length,
        )

    def format_for_llm(self) -> str:
        """Format a page for use with the LLM."""
        return "\n".join([
            f"spaceKey: {self.space_key}",
            f"pageId: {self.page_id}",
            f"title: {self.title}",
            f"author: {self.author}",
            f"created_date: {self.created_date.isoformat()}",
            f"last_updated: {self.last_updated.isoformat()}",
            f"content: {self.content}",
            f"comments: {self.comments}",
        ])

    def url(self) -> str:
        return f"{confluence_base_url}wiki/spaces/{self.space_key}/pages/{self.page_id}"
