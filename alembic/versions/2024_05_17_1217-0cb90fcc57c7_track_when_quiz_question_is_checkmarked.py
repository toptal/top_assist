"""Track when quiz question is checkmarked

Revision ID: 0cb90fcc57c7
Revises: 5704d834b7b6
Create Date: 2024-05-17 12:17:13.064814

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0cb90fcc57c7"
down_revision: str | None = "5704d834b7b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("quiz_questions", sa.Column("checked_on_slack", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("quiz_questions", "checked_on_slack")
