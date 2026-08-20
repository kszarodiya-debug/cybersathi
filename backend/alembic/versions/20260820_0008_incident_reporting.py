"""Implement incident reporting workflow and administrative audit logging."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260820_0008"
down_revision: str | None = "20260820_0007"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "incident_reports",
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "incident_reports",
        sa.Column("evidence_metadata", sa.JSON(), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE incident_reports SET occurred_at = COALESCE(created_at, now()), "
            "evidence_metadata = '{}'::json"
        )
    )
    op.alter_column(
        "incident_reports",
        "occurred_at",
        nullable=False,
        server_default=sa.text("now()"),
    )
    op.alter_column(
        "incident_reports",
        "evidence_metadata",
        nullable=False,
        server_default=sa.text("'{}'"),
    )

    op.execute(
        sa.text(
            "UPDATE incident_reports SET status = CASE status "
            "WHEN 'reported' THEN 'OPEN' "
            "WHEN 'under_review' THEN 'UNDER_REVIEW' "
            "WHEN 'resolved' THEN 'RESOLVED' "
            "WHEN 'dismissed' THEN 'REJECTED' ELSE status END, "
            "severity = UPPER(severity)"
        )
    )
    op.drop_constraint("ck_incident_reports_status", "incident_reports", type_="check")
    op.drop_constraint("ck_incident_reports_severity", "incident_reports", type_="check")
    op.create_check_constraint(
        "ck_incident_reports_status",
        "incident_reports",
        "status IN ('OPEN', 'UNDER_REVIEW', 'RESOLVED', 'REJECTED')",
    )
    op.create_check_constraint(
        "ck_incident_reports_severity",
        "incident_reports",
        "severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
    )
    op.create_index(
        "ix_incident_reports_occurred_at",
        "incident_reports",
        ["occurred_at"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"], unique=False)
    op.create_index(
        "ix_audit_logs_actor_created_at",
        "audit_logs",
        ["actor_user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_entity_created_at",
        "audit_logs",
        ["entity_type", "entity_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_entity_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_incident_reports_occurred_at", table_name="incident_reports")
    op.drop_constraint("ck_incident_reports_status", "incident_reports", type_="check")
    op.drop_constraint("ck_incident_reports_severity", "incident_reports", type_="check")
    op.create_check_constraint(
        "ck_incident_reports_status",
        "incident_reports",
        "status IN ('reported', 'under_review', 'resolved', 'dismissed')",
    )
    op.create_check_constraint(
        "ck_incident_reports_severity",
        "incident_reports",
        "severity IN ('low', 'medium', 'high', 'critical')",
    )
    op.execute(
        sa.text(
            "UPDATE incident_reports SET status = CASE status "
            "WHEN 'OPEN' THEN 'reported' WHEN 'UNDER_REVIEW' THEN 'under_review' "
            "WHEN 'RESOLVED' THEN 'resolved' WHEN 'REJECTED' THEN 'dismissed' ELSE status END, "
            "severity = LOWER(severity)"
        )
    )
    op.drop_column("incident_reports", "evidence_metadata")
    op.drop_column("incident_reports", "occurred_at")
