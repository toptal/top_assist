"""Track users awarded with luminary points

Revision ID: 5704d834b7b6
Revises: cf78760af45a
Create Date: 2024-05-16 18:03:04.764680

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5704d834b7b6"
down_revision: str | None = "cf78760af45a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("quiz_questions", sa.Column("slack_user_ids_awarded", sa.ARRAY(sa.String()), nullable=True))


def downgrade() -> None:
    op.drop_column("quiz_questions", "slack_user_ids_awarded")
