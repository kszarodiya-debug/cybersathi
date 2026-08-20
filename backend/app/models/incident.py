"""Suspicious incident report model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UpdatedAtMixin

if TYPE_CHECKING:
    from app.models.user import User


class IncidentReport(UpdatedAtMixin, Base):
    """User-submitted report of a suspicious cyber incident."""

    __tablename__ = "incident_reports"
    __table_args__ = (
        CheckConstraint(
            "status IN ('OPEN', 'UNDER_REVIEW', 'RESOLVED', 'REJECTED', 'reported', 'under_review', 'resolved', 'dismissed')",
            name="ck_incident_reports_status",
        ),
        CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'low', 'medium', 'high', 'critical')",
            name="ck_incident_reports_severity",
        ),
        Index("ix_incident_reports_status_severity", "status", "severity"),
        Index("ix_incident_reports_created_at", "created_at"),
        Index("ix_incident_reports_occurred_at", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    suspicious_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    evidence_metadata: Mapped[dict[str, str]] = mapped_column(
        JSON, nullable=False, default=dict, server_default=text("'{}'")
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
        server_default=text("'OPEN'"),
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MEDIUM",
        server_default=text("'MEDIUM'"),
    )

    user: Mapped["User"] = relationship(back_populates="incident_reports")
