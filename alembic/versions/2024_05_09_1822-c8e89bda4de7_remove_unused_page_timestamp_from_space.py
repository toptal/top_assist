"""Remove unused page timestamp from space

Revision ID: c8e89bda4de7
Revises: 79a019562e70
Create Date: 2024-05-09 18:22:01.178700

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8e89bda4de7"
down_revision: str | None = "79a019562e70"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("spaces", "last_updated_page_date")


def downgrade() -> None:
    op.add_column(
        "spaces", sa.Column("last_updated_page_date", postgresql.TIMESTAMP(), autoincrement=False, nullable=True)
    )
