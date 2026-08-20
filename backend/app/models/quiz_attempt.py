"""Quiz attempt model."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.lesson import Quiz
    from app.models.user import User


class QuizAttempt(Base):
    """A completed quiz attempt made by a user."""

    __tablename__ = "quiz_attempts"
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="ck_quiz_attempts_score_range"),
        CheckConstraint(
            "total_questions >= 0",
            name="ck_quiz_attempts_total_questions_nonnegative",
        ),
        CheckConstraint(
            "status IN ('in_progress', 'submitted')",
            name="ck_quiz_attempts_status",
        ),
        Index("ix_quiz_attempts_user_completed_at", "user_id", "completed_at"),
        Index("ix_quiz_attempts_quiz_completed_at", "quiz_id", "completed_at"),
        Index("ix_quiz_attempts_user_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quiz_id: Mapped[int] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="submitted",
        server_default=text("'submitted'"),
    )
    answers: Mapped[dict[str, str]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="quiz_attempts")
    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")
