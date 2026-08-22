"""User model and user-owned relationship definitions."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UpdatedAtMixin

if TYPE_CHECKING:
    from app.models.analysis import EmailAnalysis, URLAnalysis
    from app.models.audit import AuditLog
    from app.models.awareness import AwarenessScore
    from app.models.chat import ChatHistory
    from app.models.incident import IncidentReport
    from app.models.progress import LessonProgress
    from app.models.quiz_attempt import QuizAttempt


class User(UpdatedAtMixin, Base):
    """Student, faculty, or administrator account."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(
            "role IN ('student', 'faculty', 'admin')",
            name="ck_users_role",
        ),
        CheckConstraint(
            "year IS NULL OR year > 0",
            name="ck_users_year_positive",
        ),
        Index("ix_users_department_year", "department", "year"),
        Index("ix_users_last_login_at", "last_login_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="student",
        server_default=text("'student'"),
        index=True,
    )
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    incident_reports: Mapped[list["IncidentReport"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    url_analyses: Mapped[list["URLAnalysis"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    email_analyses: Mapped[list["EmailAnalysis"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    chat_history: Mapped[list["ChatHistory"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    awareness_score: Mapped["AwarenessScore | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    lesson_progress: Mapped[list["LessonProgress"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="actor",
        foreign_keys="AuditLog.actor_user_id",
    )
