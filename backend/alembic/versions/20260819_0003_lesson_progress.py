"""Add per-user lesson completion tracking.

Revision ID: 20260819_0003
Revises: 20260819_0002
Create Date: 2026-08-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260819_0003"
down_revision: str | None = "20260819_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lesson_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "completed = false OR completed_at IS NOT NULL",
            name="ck_lesson_progress_completed_timestamp",
        ),
        sa.ForeignKeyConstraint(["lesson_id"], ["cybersecurity_lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress_user_lesson"),
    )
    op.create_index("ix_lesson_progress_user_id", "lesson_progress", ["user_id"], unique=False)
    op.create_index("ix_lesson_progress_lesson_id", "lesson_progress", ["lesson_id"], unique=False)
    op.create_index(
        "ix_lesson_progress_user_completed",
        "lesson_progress",
        ["user_id", "completed"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_lesson_progress_user_completed", table_name="lesson_progress")
    op.drop_index("ix_lesson_progress_lesson_id", table_name="lesson_progress")
    op.drop_index("ix_lesson_progress_user_id", table_name="lesson_progress")
    op.drop_table("lesson_progress")
