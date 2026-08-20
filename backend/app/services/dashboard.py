"""Student dashboard aggregation service."""

from collections.abc import Iterable
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.analysis import EmailAnalysis, URLAnalysis
from app.models.awareness import AwarenessScore
from app.models.incident import IncidentReport
from app.models.lesson import Quiz
from app.models.progress import LessonProgress
from app.models.quiz_attempt import QuizAttempt
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.dashboard import (
    AwarenessScoreResponse,
    LearningProgressResponse,
    QuizScoreResponse,
    RecentActivityResponse,
    RecentEmailAnalysisResponse,
    RecentQuizResponse,
    RecentReportResponse,
    RecentURLAnalysisResponse,
    StudentDashboardResponse,
)


def _activity_dates(
    completed_lessons: Iterable[LessonProgress],
    quiz_timestamps: Iterable[datetime],
) -> set[date]:
    dates: set[date] = set()
    for progress in completed_lessons:
        if progress.completed_at:
            timestamp = progress.completed_at
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            dates.add(timestamp.astimezone(timezone.utc).date())
    for timestamp in quiz_timestamps:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        dates.add(timestamp.astimezone(timezone.utc).date())
    return dates


def _current_streak(activity_dates: set[date], today: date | None = None) -> int:
    if not activity_dates:
        return 0
    current_day = today or datetime.now(timezone.utc).date()
    if current_day not in activity_dates:
        current_day -= timedelta(days=1)
    streak = 0
    while current_day in activity_dates:
        streak += 1
        current_day -= timedelta(days=1)
    return streak


def build_student_dashboard(db: Session, user: User) -> StudentDashboardResponse:
    """Aggregate only records owned by the authenticated student."""

    awareness = db.scalar(
        select(AwarenessScore).where(AwarenessScore.user_id == user.id)
    )
    completed_lessons = db.scalars(
        select(LessonProgress)
        .where(
            LessonProgress.user_id == user.id,
            LessonProgress.completed.is_(True),
            LessonProgress.completed_at.is_not(None),
        )
        .order_by(desc(LessonProgress.completed_at))
    ).all()

    quiz_rows = db.execute(
        select(QuizAttempt, Quiz.title)
        .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
        .where(QuizAttempt.user_id == user.id, QuizAttempt.status == "submitted")
        .order_by(desc(QuizAttempt.completed_at))
        .limit(5)
    ).all()
    quiz_activity_timestamps = db.scalars(
        select(QuizAttempt.completed_at).where(
            QuizAttempt.user_id == user.id,
            QuizAttempt.status == "submitted",
            QuizAttempt.completed_at.is_not(None),
        )
    ).all()

    quiz_scores = [
        QuizScoreResponse(
            attempt_id=attempt.id,
            quiz_id=attempt.quiz_id,
            quiz_title=quiz_title,
            score=float(attempt.score),
            total_questions=attempt.total_questions,
            completed_at=attempt.completed_at,
        )
        for attempt, quiz_title in quiz_rows
    ]

    email_analyses = db.scalars(
        select(EmailAnalysis)
        .where(EmailAnalysis.user_id == user.id)
        .order_by(desc(EmailAnalysis.created_at))
        .limit(5)
    ).all()
    url_analyses = db.scalars(
        select(URLAnalysis)
        .where(URLAnalysis.user_id == user.id)
        .order_by(desc(URLAnalysis.created_at))
        .limit(5)
    ).all()
    reports = db.scalars(
        select(IncidentReport)
        .where(IncidentReport.user_id == user.id)
        .order_by(desc(IncidentReport.created_at))
        .limit(5)
    ).all()

    awareness_response = (
        AwarenessScoreResponse(
            overall_score=float(awareness.score),
            phishing_score=float(awareness.phishing_score),
            password_score=float(awareness.password_score),
            privacy_score=float(awareness.privacy_score),
            browsing_score=float(awareness.browsing_score),
            mobile_score=float(awareness.mobile_score),
        )
        if awareness
        else None
    )

    return StudentDashboardResponse(
        user=UserResponse.model_validate(user),
        awareness_score=awareness_response,
        learning_progress=LearningProgressResponse(
            completed_lessons=len(completed_lessons),
            quiz_scores=quiz_scores,
            current_streak=_current_streak(_activity_dates(completed_lessons, quiz_activity_timestamps)),
        ),
        recent_activity=RecentActivityResponse(
            email_analyses=[
                RecentEmailAnalysisResponse(
                    id=item.id,
                    risk_score=float(item.risk_score),
                    risk_level=item.risk_level,
                    created_at=item.created_at,
                )
                for item in email_analyses
            ],
            url_analyses=[
                RecentURLAnalysisResponse(
                    id=item.id,
                    url=item.url,
                    risk_score=float(item.risk_score),
                    risk_level=item.risk_level,
                    created_at=item.created_at,
                )
                for item in url_analyses
            ],
            quizzes=[RecentQuizResponse(**item.model_dump()) for item in quiz_scores],
            reports=[
                RecentReportResponse(
                    id=item.id,
                    incident_type=item.incident_type,
                    status=item.status,
                    severity=item.severity,
                    created_at=item.created_at,
                )
                for item in reports
            ],
        ),
    )
