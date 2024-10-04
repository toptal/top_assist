"""Space

Revision ID: 4fd21f3125fc
Revises: 0b28658a6173
Create Date: 2024-04-26 17:32:44.381629

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4fd21f3125fc"
down_revision: str | None = "0b28658a6173"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "spaces",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("space_key", sa.String(), nullable=False),
        sa.Column("space_name", sa.String(), nullable=False),
        sa.Column("last_import_date", sa.DateTime(), nullable=True),
        sa.Column("last_updated_page_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("space_key"),
        sa.UniqueConstraint("space_name"),
    )


def downgrade() -> None:
    op.drop_table("spaces")
