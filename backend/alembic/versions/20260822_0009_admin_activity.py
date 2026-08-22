"""Track the latest successful login for administrator activity summaries."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260822_0009"
down_revision: str | None = "20260820_0008"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_last_login_at", "users", ["last_login_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_last_login_at", table_name="users")
    op.drop_column("users", "last_login_at")
