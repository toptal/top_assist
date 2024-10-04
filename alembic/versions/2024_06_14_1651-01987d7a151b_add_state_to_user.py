"""Add state to User

Revision ID: 01987d7a151b
Revises: 820f66a7f6b8
Create Date: 2024-06-14 16:51:26.089372

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "01987d7a151b"
down_revision: str | None = "820f66a7f6b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("state", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "state")
