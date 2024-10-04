"""Add content length

Revision ID: 7ca9877d2017
Revises: 2fbd6fdd6bec
Create Date: 2024-08-22 15:17:35.552806

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.sql import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7ca9877d2017"
down_revision: str | None = "ef9c73e37adf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("page_data", sa.Column("content_length", sa.Integer(), nullable=True))
    conn = op.get_bind()
    batch_size = 1000
    offset = 0

    while True:
        result = conn.execute(
            text("""
                UPDATE page_data
                SET content_length = octet_length(content)
                WHERE id IN (
                    SELECT id FROM page_data ORDER BY id ASC LIMIT :batch_size OFFSET :offset
                )
            """),
            {"batch_size": batch_size, "offset": offset},
        )

        if result.rowcount == 0:
            break

        offset += batch_size

    op.alter_column("page_data", "content_length", nullable=False)


def downgrade() -> None:
    op.drop_column("page_data", "content_length")
