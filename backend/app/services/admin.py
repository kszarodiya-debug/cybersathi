"""Read models and management operations for the administrator console."""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analysis import EmailAnalysis, URLAnalysis
from app.models.awareness import AwarenessScore
from app.models.audit import AuditLog
from app.models.incident import IncidentReport
from app.models.lesson import CybersecurityLesson, Quiz, QuizQuestion
from app.models.quiz_attempt import QuizAttempt
from app.models.user import User
from app.schemas.admin import (
    AdminAnalyticsResponse,
    AdminAwarenessPoint,
    AdminCategoryPoint,
    AdminIncidentTrendPoint,
    AdminLessonSummary,
    AdminMetricSummary,
    AdminQuizPerformancePoint,
    AdminQuizSummary,
    AdminRiskPoint,
    AdminUserResponse,
    AdminUserUpdateRequest,
)


class UserManagementError(ValueError):
    """Raised when a role change would remove the last usable administrator."""


def list_users(db: Session) -> list[AdminUserResponse]:
    users = db.scalars(select(User).order_by(User.id)).all()
    return [AdminUserResponse.model_validate(user) for user in users]


def update_user(
    db: Session,
    *,
    actor_user_id: int,
    user_id: int,
    payload: AdminUserUpdateRequest,
) -> AdminUserResponse | None:
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        return None

    if payload.role is not None and payload.role != user.role:
        if user.id == actor_user_id and payload.role != "admin":
            raise UserManagementError("You cannot remove your own administrator access.")
        if user.role == "admin" and payload.role != "admin":
            admin_count = db.scalar(select(func.count()).select_from(User).where(User.role == "admin")) or 0
            if admin_count <= 1:
                raise UserManagementError("At least one administrator account must remain active.")

    changes: dict[str, str | int | None] = {}
    for field in ("role", "department", "year"):
        value = getattr(payload, field)
        if value is not None and value != getattr(user, field):
            changes[field] = value
            setattr(user, field, value)
    if not changes:
        return AdminUserResponse.model_validate(user)

    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action="update_user",
            entity_type="user",
            entity_id=user.id,
            details={"changed_fields": ",".join(sorted(changes))},
        )
    )
    db.commit()
    db.refresh(user)
    return AdminUserResponse.model_validate(user)


def list_lessons(db: Session) -> list[AdminLessonSummary]:
    rows = db.execute(
        select(
            CybersecurityLesson.id,
            CybersecurityLesson.title,
            CybersecurityLesson.category,
            CybersecurityLesson.difficulty,
            func.count(Quiz.id),
            CybersecurityLesson.created_at,
        )
        .outerjoin(Quiz, Quiz.lesson_id == CybersecurityLesson.id)
        .group_by(CybersecurityLesson.id)
        .order_by(CybersecurityLesson.id)
    ).all()
    return [
        AdminLessonSummary(
            id=row[0], title=row[1], category=row[2], difficulty=row[3], quiz_count=row[4], created_at=row[5]
        )
        for row in rows
    ]


def list_quizzes(db: Session) -> list[AdminQuizSummary]:
    question_counts = dict(
        db.execute(select(QuizQuestion.quiz_id, func.count(QuizQuestion.id)).group_by(QuizQuestion.quiz_id)).all()
    )
    attempt_counts = dict(
        db.execute(
            select(QuizAttempt.quiz_id, func.count(QuizAttempt.id))
            .where(QuizAttempt.status == "submitted")
            .group_by(QuizAttempt.quiz_id)
        ).all()
    )
    quizzes = db.scalars(select(Quiz).order_by(Quiz.id)).all()
    return [
        AdminQuizSummary(
            id=quiz.id,
            lesson_id=quiz.lesson_id,
            title=quiz.title,
            category=quiz.category,
            difficulty=quiz.difficulty,
            question_count=int(question_counts.get(quiz.id, 0)),
            attempt_count=int(attempt_counts.get(quiz.id, 0)),
        )
        for quiz in quizzes
    ]


def _count_by(db: Session, field: Any, *, where: Any | None = None) -> dict[str, int]:
    statement = select(field, func.count()).group_by(field)
    if where is not None:
        statement = statement.where(where)
    return {str(key): int(value) for key, value in db.execute(statement).all() if key is not None}


def _month_key(value: datetime) -> str:
    return value.strftime("%Y-%m")


def _last_twelve_months(now: datetime) -> list[str]:
    year, month = now.year, now.month
    months: list[str] = []
    for offset in range(11, -1, -1):
        month_index = month - offset
        current_year = year + (month_index - 1) // 12
        current_month = (month_index - 1) % 12 + 1
        months.append(f"{current_year:04d}-{current_month:02d}")
    return months


def build_analytics(db: Session) -> AdminAnalyticsResponse:
    now = datetime.now(timezone.utc)
    role_counts = _count_by(db, User.role)
    total_incidents = int(db.scalar(select(func.count()).select_from(IncidentReport)) or 0)
    open_incidents = int(
        db.scalar(
            select(func.count())
            .select_from(IncidentReport)
            .where(IncidentReport.status.in_(["OPEN", "reported"]))
        )
        or 0
    )
    high_critical_incidents = int(
        db.scalar(
            select(func.count())
            .select_from(IncidentReport)
            .where(IncidentReport.severity.in_(["HIGH", "CRITICAL", "high", "critical"]))
        )
        or 0
    )
    average_awareness = db.scalar(select(func.avg(AwarenessScore.score)))

    incident_rows = db.scalars(select(IncidentReport.created_at)).all()
    month_keys = _last_twelve_months(now)
    month_counts = {key: 0 for key in month_keys}
    for created_at in incident_rows:
        key = _month_key(created_at)
        if key in month_counts:
            month_counts[key] += 1

    awareness_columns = (
        ("Overall", AwarenessScore.score),
        ("Phishing", AwarenessScore.phishing_score),
        ("Password", AwarenessScore.password_score),
        ("Privacy", AwarenessScore.privacy_score),
        ("Browsing", AwarenessScore.browsing_score),
        ("Mobile", AwarenessScore.mobile_score),
    )
    awareness_scores = []
    for label, column in awareness_columns:
        value = db.scalar(select(func.avg(column)))
        awareness_scores.append(AdminAwarenessPoint(label=label, score=round(float(value or 0), 2)))

    quiz_rows = db.execute(
        select(Quiz.category, Quiz.title, QuizAttempt.score)
        .join(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
        .where(QuizAttempt.status == "submitted")
    ).all()
    quiz_groups: dict[str, list[float]] = defaultdict(list)
    for category, title, score in quiz_rows:
        quiz_groups[str(category or title or "General")].append(float(score))
    quiz_performance = [
        AdminQuizPerformancePoint(
            label=label,
            attempts=len(scores),
            average_score=round(sum(scores) / len(scores), 2),
        )
        for label, scores in sorted(quiz_groups.items())
    ]

    return AdminAnalyticsResponse(
        summary=AdminMetricSummary(
            total_students=role_counts.get("student", 0),
            total_faculty=role_counts.get("faculty", 0),
            total_users=sum(role_counts.values()),
            awareness_average=round(float(average_awareness or 0), 2),
            total_incidents=total_incidents,
            open_incidents=open_incidents,
            high_critical_incidents=high_critical_incidents,
            total_email_analyses=int(db.scalar(select(func.count()).select_from(EmailAnalysis)) or 0),
            total_url_analyses=int(db.scalar(select(func.count()).select_from(URLAnalysis)) or 0),
            quiz_participation=int(
                db.scalar(select(func.count()).select_from(QuizAttempt).where(QuizAttempt.status == "submitted")) or 0
            ),
        ),
        incident_trends=[AdminIncidentTrendPoint(label=key, count=month_counts[key]) for key in month_keys],
        threat_categories=[AdminCategoryPoint(label=key, count=value) for key, value in sorted(_count_by(db, IncidentReport.incident_type).items())],
        awareness_scores=awareness_scores,
        quiz_performance=quiz_performance,
        email_risk_levels=[AdminRiskPoint(label=key.upper(), count=value) for key, value in sorted(_count_by(db, EmailAnalysis.risk_level).items())],
        url_risk_levels=[AdminRiskPoint(label=key.upper(), count=value) for key, value in sorted(_count_by(db, URLAnalysis.risk_level).items())],
        generated_at=now,
    )
