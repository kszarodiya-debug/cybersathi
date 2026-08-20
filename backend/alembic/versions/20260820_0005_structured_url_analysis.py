"""Add structured fields for defensive URL analysis."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260820_0005"
down_revision: Union[str, None] = "20260820_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "url_analyses",
        sa.Column("detected_indicators", sa.JSON(), nullable=True),
    )
    op.add_column(
        "url_analyses",
        sa.Column("recommended_action", sa.Text(), nullable=True),
    )
    op.execute(
        "UPDATE url_analyses "
        "SET detected_indicators = '[]', "
        "recommended_action = 'Verify the destination independently before opening it.'"
    )
    op.alter_column(
        "url_analyses",
        "detected_indicators",
        nullable=False,
        server_default=sa.text("'[]'"),
    )
    op.alter_column("url_analyses", "recommended_action", nullable=False)
    op.drop_constraint("ck_url_analyses_risk_level", "url_analyses", type_="check")
    op.create_check_constraint(
        "ck_url_analyses_risk_level",
        "url_analyses",
        "risk_level IN ('safe', 'low', 'medium', 'high', 'critical')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_url_analyses_risk_level", "url_analyses", type_="check")
    op.create_check_constraint(
        "ck_url_analyses_risk_level",
        "url_analyses",
        "risk_level IN ('low', 'medium', 'high', 'critical')",
    )
    op.drop_column("url_analyses", "recommended_action")
    op.drop_column("url_analyses", "detected_indicators")
