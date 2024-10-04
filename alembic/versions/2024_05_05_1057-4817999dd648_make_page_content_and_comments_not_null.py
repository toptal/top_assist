"""Make page content and comments NOT NULL

Revision ID: 4817999dd648
Revises: 290dab2b2e15
Create Date: 2024-05-05 10:57:58.426584

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4817999dd648"
down_revision: str | None = "290dab2b2e15"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("page_data", "content", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("page_data", "comments", existing_type=sa.VARCHAR(), nullable=False)


def downgrade() -> None:
    op.alter_column("page_data", "comments", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("page_data", "content", existing_type=sa.VARCHAR(), nullable=True)
