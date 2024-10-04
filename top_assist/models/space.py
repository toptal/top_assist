import typing
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

from .base import Base, Mapped, Optional, int_pk, relationship, timestamp, unique_string

if TYPE_CHECKING:
    from .page_data import PageDataORM


class SpaceORM(Base):
    """SQLAlchemy model for storing Confluence space data.

    Attr:
        id: The primary key of the space.
        space_key: Confluence space key.
        space_name: Confluence space name.
        last_import_date: The timestamp of the last space import
    """

    __tablename__ = "spaces"

    id: Mapped[int_pk]
    space_key: Mapped[unique_string]
    space_name: Mapped[unique_string]
    last_import_date: Mapped[Optional[timestamp]]

    pages: Mapped[list["PageDataORM"]] = relationship(back_populates="space")

    repr_cols_num = 3


class SpaceDTO(BaseModel):
    """Data transfer object for SpaceORM.

    Attr:
        id: The primary key of the space.
        key: Confluence space key.
        name: Confluence space name.
        last_import_date: The timestamp of the last space import.
    """

    id: int_pk
    key: str
    name: str
    last_import_date: Optional[datetime]

    @classmethod
    def from_orm(cls, model: SpaceORM) -> typing.Self:
        return cls(
            id=model.id,
            key=model.space_key,
            name=model.space_name,
            last_import_date=model.last_import_date,
        )
