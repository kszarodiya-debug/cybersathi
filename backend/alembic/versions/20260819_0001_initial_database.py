"""Create the initial CyberSathi database schema.

Revision ID: 20260819_0001
Revises:
Create Date: 2026-08-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260819_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), server_default=sa.text("'student'"), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("role IN ('student', 'faculty', 'admin')", name="ck_users_role"),
        sa.CheckConstraint("year IS NULL OR year > 0", name="ck_users_year_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_role", "users", ["role"], unique=False)
    op.create_index("ix_users_department_year", "users", ["department", "year"], unique=False)

    op.create_table(
        "cybersecurity_lessons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=20), server_default=sa.text("'beginner'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced')",
            name="ck_lessons_difficulty",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cybersecurity_lessons_category", "cybersecurity_lessons", ["category"], unique=False)
    op.create_index(
        "ix_lessons_category_difficulty",
        "cybersecurity_lessons",
        ["category", "difficulty"],
        unique=False,
    )

    op.create_table(
        "quizzes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["lesson_id"], ["cybersecurity_lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quizzes_lesson_id", "quizzes", ["lesson_id"], unique=False)
    op.create_index("ix_quizzes_lesson_id_title", "quizzes", ["lesson_id", "title"], unique=False)

    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("correct_answer", sa.String(length=255), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quiz_questions_quiz_id", "quiz_questions", ["quiz_id"], unique=False)

    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_quiz_attempts_score_range"),
        sa.CheckConstraint(
            "total_questions >= 0",
            name="ck_quiz_attempts_total_questions_nonnegative",
        ),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quiz_attempts_user_id", "quiz_attempts", ["user_id"], unique=False)
    op.create_index("ix_quiz_attempts_quiz_id", "quiz_attempts", ["quiz_id"], unique=False)
    op.create_index(
        "ix_quiz_attempts_user_completed_at",
        "quiz_attempts",
        ["user_id", "completed_at"],
        unique=False,
    )
    op.create_index(
        "ix_quiz_attempts_quiz_completed_at",
        "quiz_attempts",
        ["quiz_id", "completed_at"],
        unique=False,
    )

    op.create_table(
        "incident_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("incident_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("suspicious_url", sa.String(length=2048), nullable=True),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'reported'"), nullable=False),
        sa.Column("severity", sa.String(length=20), server_default=sa.text("'medium'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('reported', 'under_review', 'resolved', 'dismissed')",
            name="ck_incident_reports_status",
        ),
        sa.CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="ck_incident_reports_severity",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incident_reports_user_id", "incident_reports", ["user_id"], unique=False)
    op.create_index("ix_incident_reports_incident_type", "incident_reports", ["incident_type"], unique=False)
    op.create_index(
        "ix_incident_reports_status_severity",
        "incident_reports",
        ["status", "severity"],
        unique=False,
    )
    op.create_index("ix_incident_reports_created_at", "incident_reports", ["created_at"], unique=False)

    op.create_table(
        "url_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("risk_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("analysis_result", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_url_analyses_risk_score_range"),
        sa.CheckConstraint(
            "risk_level IN ('low', 'medium', 'high', 'critical')",
            name="ck_url_analyses_risk_level",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_url_analyses_user_id", "url_analyses", ["user_id"], unique=False)
    op.create_index("ix_url_analyses_user_created_at", "url_analyses", ["user_id", "created_at"], unique=False)
    op.create_index("ix_url_analyses_risk_level", "url_analyses", ["risk_level"], unique=False)

    op.create_table(
        "email_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("email_content", sa.Text(), nullable=False),
        sa.Column("risk_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("analysis_result", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_email_analyses_risk_score_range"),
        sa.CheckConstraint(
            "risk_level IN ('low', 'medium', 'high', 'critical')",
            name="ck_email_analyses_risk_level",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_analyses_user_id", "email_analyses", ["user_id"], unique=False)
    op.create_index("ix_email_analyses_user_created_at", "email_analyses", ["user_id", "created_at"], unique=False)
    op.create_index("ix_email_analyses_risk_level", "email_analyses", ["risk_level"], unique=False)

    op.create_table(
        "chat_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_history_user_id", "chat_history", ["user_id"], unique=False)
    op.create_index("ix_chat_history_user_created_at", "chat_history", ["user_id", "created_at"], unique=False)

    op.create_table(
        "awareness_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("phishing_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("password_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("privacy_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("browsing_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_awareness_scores_score_range"),
        sa.CheckConstraint(
            "phishing_score >= 0 AND phishing_score <= 100",
            name="ck_awareness_scores_phishing_range",
        ),
        sa.CheckConstraint(
            "password_score >= 0 AND password_score <= 100",
            name="ck_awareness_scores_password_range",
        ),
        sa.CheckConstraint(
            "privacy_score >= 0 AND privacy_score <= 100",
            name="ck_awareness_scores_privacy_range",
        ),
        sa.CheckConstraint(
            "browsing_score >= 0 AND browsing_score <= 100",
            name="ck_awareness_scores_browsing_range",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_awareness_scores_user_id"),
    )
    op.create_index("ix_awareness_scores_user_id", "awareness_scores", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_awareness_scores_user_id", table_name="awareness_scores")
    op.drop_table("awareness_scores")

    op.drop_index("ix_chat_history_user_created_at", table_name="chat_history")
    op.drop_index("ix_chat_history_user_id", table_name="chat_history")
    op.drop_table("chat_history")

    op.drop_index("ix_email_analyses_risk_level", table_name="email_analyses")
    op.drop_index("ix_email_analyses_user_created_at", table_name="email_analyses")
    op.drop_index("ix_email_analyses_user_id", table_name="email_analyses")
    op.drop_table("email_analyses")

    op.drop_index("ix_url_analyses_risk_level", table_name="url_analyses")
    op.drop_index("ix_url_analyses_user_created_at", table_name="url_analyses")
    op.drop_index("ix_url_analyses_user_id", table_name="url_analyses")
    op.drop_table("url_analyses")

    op.drop_index("ix_incident_reports_created_at", table_name="incident_reports")
    op.drop_index("ix_incident_reports_status_severity", table_name="incident_reports")
    op.drop_index("ix_incident_reports_incident_type", table_name="incident_reports")
    op.drop_index("ix_incident_reports_user_id", table_name="incident_reports")
    op.drop_table("incident_reports")

    op.drop_index("ix_quiz_attempts_quiz_completed_at", table_name="quiz_attempts")
    op.drop_index("ix_quiz_attempts_user_completed_at", table_name="quiz_attempts")
    op.drop_index("ix_quiz_attempts_quiz_id", table_name="quiz_attempts")
    op.drop_index("ix_quiz_attempts_user_id", table_name="quiz_attempts")
    op.drop_table("quiz_attempts")

    op.drop_index("ix_quiz_questions_quiz_id", table_name="quiz_questions")
    op.drop_table("quiz_questions")

    op.drop_index("ix_quizzes_lesson_id_title", table_name="quizzes")
    op.drop_index("ix_quizzes_lesson_id", table_name="quizzes")
    op.drop_table("quizzes")

    op.drop_index("ix_lessons_category_difficulty", table_name="cybersecurity_lessons")
    op.drop_index("ix_cybersecurity_lessons_category", table_name="cybersecurity_lessons")
    op.drop_table("cybersecurity_lessons")

    op.drop_index("ix_users_department_year", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
