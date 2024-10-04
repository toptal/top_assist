"""RemoveEmbeddingsForQA

Revision ID: ef9c73e37adf
Revises: c4a3831f57ef
Create Date: 2024-07-05 20:46:29.008669

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ef9c73e37adf"
down_revision: str | None = "c4a3831f57ef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("qa_interactions", "embedded_at")


def downgrade() -> None:
    op.add_column(
        "qa_interactions",
        sa.Column("embedded_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    )
