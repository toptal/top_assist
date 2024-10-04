"""Make bookmarked conversation content nullable

Revision ID: cf78760af45a
Revises: 55d2e9ed2fe6
Create Date: 2024-05-16 17:17:40.667258

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cf78760af45a"
down_revision: str | None = "55d2e9ed2fe6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("bookmarked_conversations", "title", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("bookmarked_conversations", "body", existing_type=sa.VARCHAR(), nullable=True)


def downgrade() -> None:
    op.alter_column("bookmarked_conversations", "body", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("bookmarked_conversations", "title", existing_type=sa.VARCHAR(), nullable=False)
