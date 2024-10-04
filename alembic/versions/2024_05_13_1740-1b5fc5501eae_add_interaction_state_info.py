"""Add interaction state info

Revision ID: 1b5fc5501eae
Revises: c8e89bda4de7
Create Date: 2024-05-13 17:40:48.606297

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1b5fc5501eae"
down_revision: str | None = "c8e89bda4de7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("qa_interactions", sa.Column("answer_posted_on_slack", sa.DateTime(), nullable=True))
    op.alter_column("qa_interactions", "answer_text", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("qa_interactions", "answer_timestamp", existing_type=postgresql.TIMESTAMP(), nullable=True)


def downgrade() -> None:
    op.alter_column("qa_interactions", "answer_timestamp", existing_type=postgresql.TIMESTAMP(), nullable=False)
    op.alter_column("qa_interactions", "answer_text", existing_type=sa.VARCHAR(), nullable=False)
    op.drop_column("qa_interactions", "answer_posted_on_slack")
