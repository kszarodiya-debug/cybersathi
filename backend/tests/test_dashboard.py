from collections.abc import Iterator
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.rate_limit import auth_rate_limiter
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.analysis import EmailAnalysis, URLAnalysis
from app.models.awareness import AwarenessScore
from app.models.incident import IncidentReport
from app.models.lesson import CybersecurityLesson, Quiz
from app.models.progress import LessonProgress
from app.models.quiz_attempt import QuizAttempt
from app.models.revoked_token import RevokedToken
from app.models.user import User


@pytest.fixture
def dashboard_context(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(settings, "jwt_secret", "test-only-dashboard-secret-not-production")
    auth_rate_limiter.reset()
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Create only the tables used by this aggregation test; PostgreSQL-specific
    # JSONB tables are covered by metadata and Alembic checks elsewhere.
    for table in (
        User.__table__,
        CybersecurityLesson.__table__,
        Quiz.__table__,
        QuizAttempt.__table__,
        LessonProgress.__table__,
        AwarenessScore.__table__,
        IncidentReport.__table__,
        URLAnalysis.__table__,
        EmailAnalysis.__table__,
        RevokedToken.__table__,
    ):
        table.create(test_engine)
    test_session_factory = sessionmaker(bind=test_engine, expire_on_commit=False)

    def override_get_db() -> Iterator[Session]:
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app), test_session_factory
    finally:
        auth_rate_limiter.reset()
        app.dependency_overrides.clear()
        test_engine.dispose()


def _register(client: TestClient, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": email.split("@")[0], "email": email, "password": "StrongPassword!123"},
    )
    assert response.status_code == 201
    return response.json()


def test_dashboard_aggregates_real_user_data_without_cross_user_records(dashboard_context) -> None:
    client, session_factory = dashboard_context
    primary = _register(client, "primary@example.edu")
    secondary = _register(client, "secondary@example.edu")

    now = datetime.now(timezone.utc)
    with session_factory() as db:
        primary_user = db.query(User).filter_by(email="primary@example.edu").one()
        secondary_user = db.query(User).filter_by(email="secondary@example.edu").one()
        lesson = CybersecurityLesson(
            title="Phishing basics",
            description="Recognize suspicious messages.",
            category="phishing",
            content="Pause before you click.",
            difficulty="beginner",
        )
        quiz = Quiz(lesson=lesson, title="Phishing check", description="Test your awareness.")
        db.add_all([lesson, quiz])
        db.flush()
        primary_email = EmailAnalysis(
            user_id=primary_user.id,
            email_content="Primary private message",
            risk_score=Decimal("82.50"),
            risk_level="high",
            analysis_result="Review sender context.",
            created_at=now,
        )
        secondary_email = EmailAnalysis(
            user_id=secondary_user.id,
            email_content="Secondary private message",
            risk_score=Decimal("10.00"),
            risk_level="low",
            analysis_result="Low risk.",
            created_at=now,
        )
        primary_url = URLAnalysis(
            user_id=primary_user.id,
            url="https://campus.example.edu",
            risk_score=Decimal("12.00"),
            risk_level="low",
            analysis_result="No immediate concerns.",
            created_at=now,
        )
        secondary_report = IncidentReport(
            user_id=secondary_user.id,
            incident_type="phishing",
            description="A private report for another student.",
            status="reported",
            severity="high",
            created_at=now,
            updated_at=now,
        )
        db.add_all([
            LessonProgress(user_id=primary_user.id, lesson_id=lesson.id, completed=True, completed_at=now),
            QuizAttempt(user_id=primary_user.id, quiz_id=quiz.id, score=Decimal("90.00"), total_questions=5, completed_at=now),
            AwarenessScore(
                user_id=primary_user.id,
                score=Decimal("88.00"),
                phishing_score=Decimal("84.00"),
                password_score=Decimal("92.00"),
                privacy_score=Decimal("86.00"),
                browsing_score=Decimal("90.00"),
            ),
            primary_email,
            secondary_email,
            primary_url,
            secondary_report,
        ])
        db.commit()
        primary_email_id = primary_email.id
        primary_url_id = primary_url.id

    response = client.get(
        "/api/v1/students/dashboard",
        headers={"Authorization": f"Bearer {primary['access_token']}"},
    )

    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["user"]["email"] == "primary@example.edu"
    assert dashboard["awareness_score"]["overall_score"] == 88.0
    assert dashboard["learning_progress"]["completed_lessons"] == 1
    assert dashboard["learning_progress"]["quiz_scores"][0]["score"] == 90.0
    assert dashboard["learning_progress"]["current_streak"] >= 1
    assert [item["id"] for item in dashboard["recent_activity"]["email_analyses"]] == [primary_email_id]
    assert [item["id"] for item in dashboard["recent_activity"]["url_analyses"]] == [primary_url_id]
    assert dashboard["recent_activity"]["reports"] == []


def test_dashboard_returns_empty_states_when_no_data_exists(dashboard_context) -> None:
    client, _ = dashboard_context
    user = _register(client, "empty@example.edu")

    response = client.get(
        "/api/v1/students/dashboard",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )

    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["awareness_score"] is None
    assert dashboard["learning_progress"] == {
        "completed_lessons": 0,
        "quiz_scores": [],
        "current_streak": 0,
    }
    assert dashboard["recent_activity"] == {
        "email_analyses": [],
        "url_analyses": [],
        "quizzes": [],
        "reports": [],
    }


def test_dashboard_rejects_non_student_roles(dashboard_context) -> None:
    client, session_factory = dashboard_context
    _register(client, "faculty@example.edu")
    with session_factory() as db:
        user = db.query(User).filter_by(email="faculty@example.edu").one()
        user.role = "faculty"
        db.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "faculty@example.edu", "password": "StrongPassword!123"},
    )
    assert login.status_code == 200

    response = client.get(
        "/api/v1/students/dashboard",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert response.status_code == 403
