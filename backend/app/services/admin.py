"""Read models and management operations for the administrator console."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from math import ceil
from typing import Any, Literal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analysis import EmailAnalysis, URLAnalysis
from app.models.awareness import AwarenessScore
from app.models.audit import AuditLog
from app.models.incident import IncidentReport
from app.models.lesson import CybersecurityLesson, Quiz, QuizQuestion
from app.models.progress import LessonProgress
from app.models.quiz_attempt import QuizAttempt
from app.models.user import User
from app.schemas.admin import (
    AdminActivityItem,
    AdminActivityResponse,
    AdminAnalyticsResponse,
    AdminAwarenessPoint,
    AdminCategoryPoint,
    AdminIncidentTrendPoint,
    AdminLessonSummary,
    AdminMetricSummary,
    AdminQuizPerformancePoint,
    AdminQuizSummary,
    AdminRiskPoint,
    AdminStatsResponse,
    AdminTimeSeriesPoint,
    AdminUserDetailResponse,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdateRequest,
)


class UserManagementError(ValueError):
    """Raised when a role change would remove the last usable administrator."""


def _user_progress_statement():
    lessons = (
        select(LessonProgress.user_id.label("progress_user_id"), func.count(LessonProgress.id).label("lessons_completed"))
        .where(LessonProgress.completed.is_(True))
        .group_by(LessonProgress.user_id)
        .subquery()
    )
    attempts = (
        select(
            QuizAttempt.user_id.label("attempt_user_id"),
            func.count(QuizAttempt.id).label("quiz_attempts"),
            func.avg(QuizAttempt.score).label("average_quiz_score"),
        )
        .where(QuizAttempt.status == "submitted")
        .group_by(QuizAttempt.user_id)
        .subquery()
    )
    return (
        select(
            User,
            lessons.c.lessons_completed,
            attempts.c.quiz_attempts,
            attempts.c.average_quiz_score,
            AwarenessScore.score,
            AwarenessScore.phishing_score,
            AwarenessScore.password_score,
            AwarenessScore.privacy_score,
            AwarenessScore.browsing_score,
        )
        .outerjoin(lessons, lessons.c.progress_user_id == User.id)
        .outerjoin(attempts, attempts.c.attempt_user_id == User.id)
        .outerjoin(AwarenessScore, AwarenessScore.user_id == User.id)
    )


def _user_response(row: Any) -> AdminUserResponse:
    user = row[0]
    return AdminUserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        department=user.department,
        year=user.year,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
        lessons_completed=int(row[1] or 0),
        quiz_attempts=int(row[2] or 0),
        average_quiz_score=round(float(row[3] or 0), 2),
        awareness_score=float(row[4]) if row[4] is not None else None,
        phishing_score=float(row[5]) if row[5] is not None else None,
        password_score=float(row[6]) if row[6] is not None else None,
        privacy_score=float(row[7]) if row[7] is not None else None,
        browsing_score=float(row[8]) if row[8] is not None else None,
    )


def _basic_user_response(user: User) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        department=user.department,
        year=user.year,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


def list_users(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 25,
    search: str | None = None,
    role: str | None = None,
    department: str | None = None,
    sort: Literal["created_at_asc", "created_at_desc"] = "created_at_desc",
) -> AdminUserListResponse:
    """Return privacy-minimized, aggregate user progress with bounded pagination."""

    filters = []
    if search:
        filters.append(or_(User.name.contains(search, autoescape=True), User.email.contains(search, autoescape=True)))
    if role:
        filters.append(User.role == role)
    if department:
        filters.append(User.department == department)

    total = int(db.scalar(select(func.count()).select_from(User).where(*filters)) or 0)
    order_column = User.created_at.asc() if sort == "created_at_asc" else User.created_at.desc()
    rows = db.execute(
        _user_progress_statement().where(*filters).order_by(order_column, User.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return AdminUserListResponse(
        users=[_user_response(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


def get_user_detail(db: Session, *, user_id: int) -> AdminUserDetailResponse | None:
    row = db.execute(_user_progress_statement().where(User.id == user_id)).first()
    if row is None:
        return None
    summary = _user_response(row)
    activity_specs = (
        ("quiz_attempts", QuizAttempt, QuizAttempt.completed_at, QuizAttempt.status == "submitted"),
        ("lesson_completions", LessonProgress, LessonProgress.completed_at, LessonProgress.completed.is_(True)),
        ("email_analyses", EmailAnalysis, EmailAnalysis.created_at, None),
        ("url_analyses", URLAnalysis, URLAnalysis.created_at, None),
        ("incident_reports", IncidentReport, IncidentReport.created_at, None),
    )
    activity: list[AdminActivityItem] = []
    for label, model, timestamp_column, condition in activity_specs:
        predicates = [model.user_id == user_id, timestamp_column.is_not(None)]
        if condition is not None:
            predicates.append(condition)
        count, latest = db.execute(select(func.count(model.id), func.max(timestamp_column)).where(*predicates)).one()
        activity.append(AdminActivityItem(activity_type=label, count=int(count or 0), latest_at=latest))
    return AdminUserDetailResponse(**summary.model_dump(), recent_activity=activity)


def update_user(db: Session, *, actor_user_id: int, user_id: int, payload: AdminUserUpdateRequest) -> AdminUserResponse | None:
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        return None
    if payload.role is not None and payload.role != user.role:
        if payload.role == "admin" and user.role != "admin":
            designated_email = str(settings.admin_email).strip().lower() if settings.admin_email else None
            if designated_email is None or user.email.lower() != designated_email:
                raise UserManagementError("Only the configured designated administrator may hold this role.")
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
        return _basic_user_response(user)
    db.add(AuditLog(actor_user_id=actor_user_id, action="update_user", entity_type="user", entity_id=user.id, details={"changed_fields": ",".join(sorted(changes))}))
    db.commit()
    db.refresh(user)
    return _basic_user_response(user)


def list_lessons(db: Session) -> list[AdminLessonSummary]:
    rows = db.execute(
        select(CybersecurityLesson.id, CybersecurityLesson.title, CybersecurityLesson.category, CybersecurityLesson.difficulty, func.count(Quiz.id), CybersecurityLesson.created_at)
        .outerjoin(Quiz, Quiz.lesson_id == CybersecurityLesson.id)
        .group_by(CybersecurityLesson.id)
        .order_by(CybersecurityLesson.id)
    ).all()
    return [AdminLessonSummary(id=row[0], title=row[1], category=row[2], difficulty=row[3], quiz_count=row[4], created_at=row[5]) for row in rows]


def list_quizzes(db: Session) -> list[AdminQuizSummary]:
    question_counts = dict(db.execute(select(QuizQuestion.quiz_id, func.count(QuizQuestion.id)).group_by(QuizQuestion.quiz_id)).all())
    attempt_counts = dict(db.execute(select(QuizAttempt.quiz_id, func.count(QuizAttempt.id)).where(QuizAttempt.status == "submitted").group_by(QuizAttempt.quiz_id)).all())
    quizzes = db.scalars(select(Quiz).order_by(Quiz.id)).all()
    return [AdminQuizSummary(id=quiz.id, lesson_id=quiz.lesson_id, title=quiz.title, category=quiz.category, difficulty=quiz.difficulty, question_count=int(question_counts.get(quiz.id, 0)), attempt_count=int(attempt_counts.get(quiz.id, 0))) for quiz in quizzes]


def _count_by(db: Session, field: Any, *, where: Any | None = None) -> dict[str, int]:
    statement = select(field, func.count()).group_by(field)
    if where is not None:
        statement = statement.where(where)
    return {str(key): int(value) for key, value in db.execute(statement).all() if key is not None}


def get_admin_stats(db: Session) -> AdminStatsResponse:
    now = datetime.now(timezone.utc)
    active_since = now - timedelta(days=30)
    role_counts = _count_by(db, User.role)
    awareness_average = db.scalar(select(func.avg(AwarenessScore.score)))
    return AdminStatsResponse(
        registered_users=sum(role_counts.values()),
        active_users=int(db.scalar(select(func.count()).select_from(User).where(User.last_login_at >= active_since)) or 0),
        students=role_counts.get("student", 0),
        faculty=role_counts.get("faculty", 0),
        admins=role_counts.get("admin", 0),
        total_quiz_attempts=int(db.scalar(select(func.count()).select_from(QuizAttempt).where(QuizAttempt.status == "submitted")) or 0),
        total_incident_reports=int(db.scalar(select(func.count()).select_from(IncidentReport)) or 0),
        total_email_analyses=int(db.scalar(select(func.count()).select_from(EmailAnalysis)) or 0),
        total_url_analyses=int(db.scalar(select(func.count()).select_from(URLAnalysis)) or 0),
        awareness_average=round(float(awareness_average or 0), 2),
        generated_at=now,
    )


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _daily_series(db: Session, model: Any, timestamp_column: Any, *, condition: Any | None = None) -> list[AdminTimeSeriesPoint]:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=29)).date()
    labels = [(start + timedelta(days=offset)).isoformat() for offset in range(30)]
    predicates = [timestamp_column.is_not(None), timestamp_column >= datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)]
    if condition is not None:
        predicates.append(condition)
    values = db.scalars(select(timestamp_column).select_from(model).where(*predicates)).all()
    counts = dict.fromkeys(labels, 0)
    for value in values:
        key = _as_utc(value).date().isoformat()
        if key in counts:
            counts[key] += 1
    return [AdminTimeSeriesPoint(label=key, count=counts[key]) for key in labels]


def build_activity(db: Session) -> AdminActivityResponse:
    return AdminActivityResponse(
        registrations=_daily_series(db, User, User.created_at),
        quiz_activity=_daily_series(db, QuizAttempt, QuizAttempt.completed_at, condition=QuizAttempt.status == "submitted"),
        lesson_completions=_daily_series(db, LessonProgress, LessonProgress.completed_at, condition=LessonProgress.completed.is_(True)),
        email_analyses=_daily_series(db, EmailAnalysis, EmailAnalysis.created_at),
        url_analyses=_daily_series(db, URLAnalysis, URLAnalysis.created_at),
        incident_reports=_daily_series(db, IncidentReport, IncidentReport.created_at),
        generated_at=datetime.now(timezone.utc),
    )


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
    stats = get_admin_stats(db)
    role_counts = _count_by(db, User.role)
    total_incidents = stats.total_incident_reports
    open_incidents = int(db.scalar(select(func.count()).select_from(IncidentReport).where(func.upper(IncidentReport.status).in_(["OPEN", "REPORTED"]))) or 0)
    high_critical_incidents = int(db.scalar(select(func.count()).select_from(IncidentReport).where(func.upper(IncidentReport.severity).in_(["HIGH", "CRITICAL"]))) or 0)
    incident_rows = db.scalars(select(IncidentReport.created_at)).all()
    month_keys = _last_twelve_months(now)
    month_counts = {key: 0 for key in month_keys}
    for created_at in incident_rows:
        key = _month_key(created_at)
        if key in month_counts:
            month_counts[key] += 1

    awareness_columns = (("Overall", AwarenessScore.score), ("Phishing", AwarenessScore.phishing_score), ("Password", AwarenessScore.password_score), ("Privacy", AwarenessScore.privacy_score), ("Browsing", AwarenessScore.browsing_score), ("Mobile", AwarenessScore.mobile_score))
    awareness_scores = [AdminAwarenessPoint(label=label, score=round(float(db.scalar(select(func.avg(column))) or 0), 2)) for label, column in awareness_columns]
    quiz_rows = db.execute(select(Quiz.category, Quiz.title, QuizAttempt.score).join(QuizAttempt, QuizAttempt.quiz_id == Quiz.id).where(QuizAttempt.status == "submitted")).all()
    quiz_groups: dict[str, list[float]] = defaultdict(list)
    for category, title, score in quiz_rows:
        quiz_groups[str(category or title or "General")].append(float(score))
    quiz_performance = [AdminQuizPerformancePoint(label=label, attempts=len(scores), average_score=round(sum(scores) / len(scores), 2)) for label, scores in sorted(quiz_groups.items())]
    awareness_distribution = []
    for lower, upper in ((0, 20), (21, 40), (41, 60), (61, 80), (81, 100)):
        count = int(db.scalar(select(func.count()).select_from(AwarenessScore).where(AwarenessScore.score.between(lower, upper))) or 0)
        awareness_distribution.append(AdminCategoryPoint(label=f"{lower}-{upper}", count=count))

    return AdminAnalyticsResponse(
        summary=AdminMetricSummary(total_students=role_counts.get("student", 0), total_faculty=role_counts.get("faculty", 0), total_users=stats.registered_users, awareness_average=stats.awareness_average, total_incidents=total_incidents, open_incidents=open_incidents, high_critical_incidents=high_critical_incidents, total_email_analyses=stats.total_email_analyses, total_url_analyses=stats.total_url_analyses, quiz_participation=stats.total_quiz_attempts, active_users=stats.active_users, registered_users=stats.registered_users, total_quiz_attempts=stats.total_quiz_attempts, total_incident_reports=stats.total_incident_reports),
        incident_trends=[AdminIncidentTrendPoint(label=key, count=month_counts[key]) for key in month_keys],
        threat_categories=[AdminCategoryPoint(label=key, count=value) for key, value in sorted(_count_by(db, IncidentReport.incident_type).items())],
        awareness_scores=awareness_scores,
        quiz_performance=quiz_performance,
        email_risk_levels=[AdminRiskPoint(label=key.upper(), count=value) for key, value in sorted(_count_by(db, EmailAnalysis.risk_level).items())],
        url_risk_levels=[AdminRiskPoint(label=key.upper(), count=value) for key, value in sorted(_count_by(db, URLAnalysis.risk_level).items())],
        generated_at=now,
        awareness_distribution=awareness_distribution,
        phishing_reports=int(db.scalar(select(func.count()).select_from(IncidentReport).where(func.lower(IncidentReport.incident_type).contains("phish"))) or 0),
        suspicious_url_analyses=int(db.scalar(select(func.count()).select_from(URLAnalysis).where(func.lower(URLAnalysis.risk_level) != "safe")) or 0),
        high_risk_url_analyses=int(db.scalar(select(func.count()).select_from(URLAnalysis).where(func.lower(URLAnalysis.risk_level).in_(["high", "critical"]))) or 0),
        high_risk_email_analyses=int(db.scalar(select(func.count()).select_from(EmailAnalysis).where(func.lower(EmailAnalysis.risk_level).in_(["high", "critical"]))) or 0),
        cyber_incidents=total_incidents,
    )
