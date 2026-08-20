"""User lesson completion tracking."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UpdatedAtMixin

if TYPE_CHECKING:
    from app.models.lesson import CybersecurityLesson
    from app.models.user import User


class LessonProgress(UpdatedAtMixin, Base):
    """Completion state for one lesson belonging to one user."""

    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress_user_lesson"),
        CheckConstraint(
            "completed = false OR completed_at IS NOT NULL",
            name="ck_lesson_progress_completed_timestamp",
        ),
        Index("ix_lesson_progress_user_completed", "user_id", "completed"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("cybersecurity_lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="lesson_progress")
    lesson: Mapped["CybersecurityLesson"] = relationship(back_populates="progress_records")
