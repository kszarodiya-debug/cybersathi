"""Cybersecurity lessons, quizzes, and quiz questions."""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, JSON, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.progress import LessonProgress
    from app.models.quiz_attempt import QuizAttempt


class CybersecurityLesson(CreatedAtMixin, Base):
    """Educational content grouped by category and difficulty."""

    __tablename__ = "cybersecurity_lessons"
    __table_args__ = (
        CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced')",
            name="ck_lessons_difficulty",
        ),
        Index("ix_lessons_category_difficulty", "category", "difficulty"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    introduction: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'A practical introduction to this cybersecurity topic.'"),
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    learning_objectives: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list, server_default=text("'[]'")
    )
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'Review the practical guidance in this lesson.'"),
    )
    real_world_example: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'Use the safety tips to evaluate an unexpected request.'"),
    )
    safety_tips: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list, server_default=text("'[]'")
    )
    key_takeaways: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list, server_default=text("'[]'")
    )
    difficulty: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="beginner",
        server_default=text("'beginner'"),
    )

    quizzes: Mapped[list["Quiz"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    progress_records: Mapped[list["LessonProgress"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Quiz(Base):
    """Quiz associated with a cybersecurity lesson."""

    __tablename__ = "quizzes"
    __table_args__ = (
        CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced')",
            name="ck_quizzes_difficulty",
        ),
        Index("ix_quizzes_lesson_id_title", "lesson_id", "title"),
        Index("ix_quizzes_category_difficulty", "category", "difficulty"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("cybersecurity_lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(100), nullable=False, default="general", server_default=text("'general'"), index=True
    )
    difficulty: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="beginner",
        server_default=text("'beginner'"),
    )

    lesson: Mapped["CybersecurityLesson"] = relationship(back_populates="quizzes")
    questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="quiz",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="quiz",
        passive_deletes=True,
    )


class QuizQuestion(Base):
    """A multiple-choice or structured question belonging to a quiz."""

    __tablename__ = "quiz_questions"
    __table_args__ = (
        Index("ix_quiz_questions_quiz_id", "quiz_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")
