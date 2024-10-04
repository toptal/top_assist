"""Initial migration

Revision ID: 713caec2649e
Revises:
Create Date: 2024-04-12 13:54:12.213839

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "713caec2649e"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
