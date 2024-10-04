from datetime import UTC, datetime
from typing import Annotated, Optional

from sqlalchemy import ARRAY, DateTime, ForeignKey, Index, Integer, String, UnaryExpression
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Custom types
int_pk = Annotated[int, mapped_column(Integer, primary_key=True)]
thread_id = Annotated[str, mapped_column(String(17), index=True)]
score = Annotated[int, mapped_column(Integer, default=0)]
unique_string = Annotated[str, mapped_column(String, unique=True, nullable=False)]
slack_user_ids = Annotated[list[str], mapped_column(ARRAY(String), nullable=True)]


def lazy_utc_now() -> datetime:
    return datetime.now(UTC)


created_at = Annotated[datetime, mapped_column(DateTime(timezone=True), nullable=False, default=lazy_utc_now)]
updated_at = Annotated[
    datetime, mapped_column(DateTime(timezone=True), nullable=False, default=lazy_utc_now, onupdate=lazy_utc_now)
]
timestamp = Annotated[datetime, mapped_column(DateTime(timezone=True))]


class TimestampMixin:
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class Base(DeclarativeBase, TimestampMixin):
    """Base class for all SQLAlchemy models."""

    repr_cols_num = 1  # First N columns of the table to include in __repr__ by default
    repr_cols: tuple[str, ...] = ()  # Columns to include to __repr__ additionally

    def __repr__(self):
        """Return a string representation of the object.

        Returns:
            <ClassName col1=val1, col2=val2, ...>
        """
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f'<{self.__class__.__name__} {", ".join(cols)}>'


__all__ = [
    "Base",
    "int_pk",
    "thread_id",
    "score",
    "unique_string",
    "Optional",
    "Index",
    "DateTime",
    "datetime",
    "mapped_column",
    "Mapped",
    "ForeignKey",
    "relationship",
    "UnaryExpression",
    "slack_user_ids",
    "timestamp",
    "Annotated",
    "Integer",
]
