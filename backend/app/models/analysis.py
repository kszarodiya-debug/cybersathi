"""Suspicious URL and email analysis models."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, JSON, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.user import User


class URLAnalysis(CreatedAtMixin, Base):
    """Non-invasive defensive analysis result for a URL submitted by a user."""

    __tablename__ = "url_analyses"
    __table_args__ = (
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_url_analyses_risk_score_range"),
        CheckConstraint(
            "risk_level IN ('safe', 'low', 'medium', 'high', 'critical')",
            name="ck_url_analyses_risk_level",
        ),
        Index("ix_url_analyses_user_created_at", "user_id", "created_at"),
        Index("ix_url_analyses_risk_level", "risk_level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    analysis_result: Mapped[str] = mapped_column(Text, nullable=False)
    detected_indicators: Mapped[list[dict[str, str]]] = mapped_column(
        JSON, nullable=False, default=list, server_default=text("'[]'")
    )
    recommended_action: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'Verify the destination independently before opening it.'"),
    )

    user: Mapped["User"] = relationship(back_populates="url_analyses")


class EmailAnalysis(CreatedAtMixin, Base):
    """Defensive analysis result for email or message content submitted by a user."""

    __tablename__ = "email_analyses"
    __table_args__ = (
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_email_analyses_risk_score_range"),
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high', 'critical')",
            name="ck_email_analyses_risk_level",
        ),
        CheckConstraint(
            "content_type IN ('email', 'sms', 'whatsapp', 'social_media')",
            name="ck_email_analyses_content_type",
        ),
        Index("ix_email_analyses_user_created_at", "user_id", "created_at"),
        Index("ix_email_analyses_risk_level", "risk_level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="email", server_default=text("'email'")
    )
    email_content: Mapped[str] = mapped_column(Text, nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    analysis_result: Mapped[str] = mapped_column(Text, nullable=False)
    detected_indicators: Mapped[list[dict[str, str]]] = mapped_column(
        JSON, nullable=False, default=list, server_default=text("'[]'")
    )
    recommended_actions: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list, server_default=text("'[]'")
    )
    safe_handling_advice: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'Do not click links or share secrets until independently verified.'"),
    )

    user: Mapped["User"] = relationship(back_populates="email_analyses")
