"""Declarative metadata used by SQLAlchemy and Alembic."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


# Import models after Base exists so every model is registered in metadata.
from app.models.awareness import AwarenessScore  # noqa: E402,F401
from app.models.chat import ChatHistory  # noqa: E402,F401
from app.models.incident import IncidentReport  # noqa: E402,F401
from app.models.lesson import CybersecurityLesson, Quiz, QuizQuestion  # noqa: E402,F401
from app.models.quiz_attempt import QuizAttempt  # noqa: E402,F401
from app.models.progress import LessonProgress  # noqa: E402,F401
from app.models.revoked_token import RevokedToken  # noqa: E402,F401
from app.models.analysis import EmailAnalysis, URLAnalysis  # noqa: E402,F401
from app.models.audit import AuditLog  # noqa: E402,F401
from app.models.user import User  # noqa: E402,F401
