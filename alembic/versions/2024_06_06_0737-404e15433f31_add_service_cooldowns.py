"""Add service cooldowns

Revision ID: 404e15433f31
Revises: 89e5323369b9
Create Date: 2024-06-06 07:37:34.885754

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "404e15433f31"
down_revision: str | None = "89e5323369b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_cooldowns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_key", sa.String(), nullable=False),
        sa.Column("cooldown_seconds", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_key"),
    )


def downgrade() -> None:
    op.drop_table("service_cooldowns")
