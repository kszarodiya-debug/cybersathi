"""Current cybersecurity awareness score per user."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UpdatedAtMixin

if TYPE_CHECKING:
    from app.models.user import User


class AwarenessScore(UpdatedAtMixin, Base):
    """Aggregated awareness score and category scores for one user."""

    __tablename__ = "awareness_scores"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_awareness_scores_user_id"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_awareness_scores_score_range"),
        CheckConstraint(
            "phishing_score >= 0 AND phishing_score <= 100",
            name="ck_awareness_scores_phishing_range",
        ),
        CheckConstraint(
            "password_score >= 0 AND password_score <= 100",
            name="ck_awareness_scores_password_range",
        ),
        CheckConstraint(
            "privacy_score >= 0 AND privacy_score <= 100",
            name="ck_awareness_scores_privacy_range",
        ),
        CheckConstraint(
            "browsing_score >= 0 AND browsing_score <= 100",
            name="ck_awareness_scores_browsing_range",
        ),
        CheckConstraint(
            "mobile_score >= 0 AND mobile_score <= 100",
            name="ck_awareness_scores_mobile_range",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    phishing_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    password_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    privacy_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    browsing_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    mobile_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=0, server_default="0"
    )

    user: Mapped["User"] = relationship(back_populates="awareness_score")
