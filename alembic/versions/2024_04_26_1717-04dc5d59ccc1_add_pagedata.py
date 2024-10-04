"""Add PageData

Revision ID: 04dc5d59ccc1
Revises: 713caec2649e
Create Date: 2024-04-26 17:17:34.626120

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "04dc5d59ccc1"
down_revision: str | None = "713caec2649e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "page_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.String(), nullable=False),
        sa.Column("space_key", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("author", sa.String(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=False),
        sa.Column("last_updated", sa.DateTime(), nullable=False),
        sa.Column("content", sa.String(), nullable=True),
        sa.Column("comments", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("page_id"),
    )
    op.create_index("ix_page_data_page_id", "page_data", ["page_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_page_data_page_id", table_name="page_data")
    op.drop_table("page_data")
