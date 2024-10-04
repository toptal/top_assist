"""Add embedded timestamp to QA

Revision ID: 55d2e9ed2fe6
Revises: c8e89bda4de7
Create Date: 2024-05-14 13:34:20.809805

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "55d2e9ed2fe6"
down_revision: str | None = "f87f24dea885"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("qa_interactions", sa.Column("embedded_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("qa_interactions", "embedded_at")
