"""Add posted Confluence page ids

Revision ID: 79a019562e70
Revises: 4817999dd648
Create Date: 2024-05-09 18:17:43.543302

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "79a019562e70"
down_revision: str | None = "4817999dd648"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bookmarked_conversations", sa.Column("page_id", sa.String(), nullable=True))
    op.add_column("quiz_questions", sa.Column("page_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("quiz_questions", "page_id")
    op.drop_column("bookmarked_conversations", "page_id")
