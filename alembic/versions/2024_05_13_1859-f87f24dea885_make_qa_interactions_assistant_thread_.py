"""Make qa_interactions.assistant_thread_id nullable

Revision ID: f87f24dea885
Revises: 1b5fc5501eae
Create Date: 2024-05-13 18:59:05.196845

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f87f24dea885"
down_revision: str | None = "1b5fc5501eae"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("qa_interactions", "assistant_thread_id", existing_type=sa.VARCHAR(), nullable=True)


def downgrade() -> None:
    op.alter_column("qa_interactions", "assistant_thread_id", existing_type=sa.VARCHAR(), nullable=False)
