"""Add structured fields for defensive email and message analysis."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260820_0004"
down_revision: Union[str, None] = "20260819_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "email_analyses",
        sa.Column("content_type", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "email_analyses",
        sa.Column("detected_indicators", sa.JSON(), nullable=True),
    )
    op.add_column(
        "email_analyses",
        sa.Column("recommended_actions", sa.JSON(), nullable=True),
    )
    op.add_column(
        "email_analyses",
        sa.Column("safe_handling_advice", sa.Text(), nullable=True),
    )
    op.execute(
        "UPDATE email_analyses "
        "SET content_type = 'email', detected_indicators = '[]', "
        "recommended_actions = '[]', "
        "safe_handling_advice = 'Do not click links or share secrets until independently verified.'"
    )
    op.alter_column(
        "email_analyses",
        "content_type",
        nullable=False,
        server_default=sa.text("'email'"),
    )
    op.alter_column(
        "email_analyses",
        "detected_indicators",
        nullable=False,
        server_default=sa.text("'[]'"),
    )
    op.alter_column(
        "email_analyses",
        "recommended_actions",
        nullable=False,
        server_default=sa.text("'[]'"),
    )
    op.alter_column("email_analyses", "safe_handling_advice", nullable=False)
    op.create_check_constraint(
        "ck_email_analyses_content_type",
        "email_analyses",
        "content_type IN ('email', 'sms', 'whatsapp', 'social_media')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_email_analyses_content_type", "email_analyses", type_="check")
    op.drop_column("email_analyses", "safe_handling_advice")
    op.drop_column("email_analyses", "recommended_actions")
    op.drop_column("email_analyses", "detected_indicators")
    op.drop_column("email_analyses", "content_type")
