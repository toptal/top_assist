"""Relationship Space PageData

Revision ID: 290dab2b2e15
Revises: eda3f2766ce1
Create Date: 2024-04-30 11:04:48.466660

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "290dab2b2e15"
down_revision: str | None = "eda3f2766ce1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("page_data", sa.Column("space_id", sa.Integer(), nullable=False))
    op.create_foreign_key("fk_page_data_spaces", "page_data", "spaces", ["space_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_page_data_spaces", "page_data", type_="foreignkey")
    op.drop_column("page_data", "space_id")
