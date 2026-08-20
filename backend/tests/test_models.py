from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.models import (
    AwarenessScore,
    AuditLog,
    ChatHistory,
    CybersecurityLesson,
    EmailAnalysis,
    IncidentReport,
    Quiz,
    QuizAttempt,
    QuizQuestion,
    URLAnalysis,
    User,
)


EXPECTED_TABLES = {
    "users",
    "cybersecurity_lessons",
    "quizzes",
    "quiz_questions",
    "quiz_attempts",
    "incident_reports",
    "url_analyses",
    "email_analyses",
    "chat_history",
    "awareness_scores",
    "audit_logs",
    "revoked_tokens",
    "lesson_progress",
}


def test_all_database_models_are_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_core_relationships_are_configured() -> None:
    assert User.quiz_attempts.property.back_populates == "user"
    assert User.awareness_score.property.uselist is False
    assert CybersecurityLesson.quizzes.property.back_populates == "lesson"
    assert Quiz.questions.property.back_populates == "quiz"
    assert QuizAttempt.user.property.back_populates == "quiz_attempts"
    assert IncidentReport.user.property.back_populates == "incident_reports"
    assert URLAnalysis.user.property.back_populates == "url_analyses"
    assert EmailAnalysis.user.property.back_populates == "email_analyses"
    assert ChatHistory.user.property.back_populates == "chat_history"
    assert AwarenessScore.user.property.back_populates == "awareness_score"
    assert AuditLog.actor.property.back_populates == "audit_logs"


def test_postgresql_specific_quiz_options_type_and_constraints() -> None:
    assert isinstance(QuizQuestion.__table__.c.options.type, JSONB)

    constraint_names = {
        constraint.name
        for table in Base.metadata.tables.values()
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert {
        "ck_users_role",
        "ck_incident_reports_status",
        "ck_incident_reports_severity",
        "ck_url_analyses_risk_score_range",
        "ck_awareness_scores_score_range",
    }.issubset(constraint_names)
