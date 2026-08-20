from collections.abc import Iterator
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.passwords import hash_password
from app.auth.rate_limit import auth_rate_limiter
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.analysis import EmailAnalysis, URLAnalysis
from app.models.audit import AuditLog
from app.models.awareness import AwarenessScore
from app.models.incident import IncidentReport
from app.models.lesson import CybersecurityLesson, Quiz, QuizQuestion
from app.models.quiz_attempt import QuizAttempt
from app.models.revoked_token import RevokedToken
from app.models.user import User


@pytest.fixture
def admin_context(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(settings, "jwt_secret", "test-only-admin-secret-not-production")
    auth_rate_limiter.reset()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    original_options_type = QuizQuestion.__table__.c.options.type
    QuizQuestion.__table__.c.options.type = JSON()
    try:
        for table in (
            User.__table__, CybersecurityLesson.__table__, Quiz.__table__, QuizQuestion.__table__,
            QuizAttempt.__table__, IncidentReport.__table__, AwarenessScore.__table__,
            EmailAnalysis.__table__, URLAnalysis.__table__, AuditLog.__table__, RevokedToken.__table__,
        ):
            table.create(engine)
    finally:
        QuizQuestion.__table__.c.options.type = original_options_type
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db() -> Iterator[Session]:
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app), factory
    finally:
        auth_rate_limiter.reset()
        app.dependency_overrides.clear()
        QuizQuestion.__table__.c.options.type = original_options_type
        engine.dispose()


def _session(client: TestClient, email: str, role: str = "student") -> dict:
    if role == "student":
        response = client.post(
            "/api/v1/auth/register",
            json={"name": email.split("@")[0], "email": email, "password": "StrongPassword!123"},
        )
        assert response.status_code == 201
        return response.json()
    raise AssertionError("Use the fixture database to create privileged users.")


def _headers(session: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['access_token']}"}


def test_admin_analytics_is_role_protected_and_aggregate_only(admin_context) -> None:
    client, factory = admin_context
    student = _session(client, "student@example.edu")
    with factory() as db:
        admin = User(name="Admin", email="admin@example.edu", password_hash=hash_password("AdminPassword!123"), role="admin")
        faculty = User(name="Faculty", email="faculty@example.edu", password_hash=hash_password("FacultyPassword!123"), role="faculty")
        db.add_all([admin, faculty])
        db.commit()

    forbidden = client.get("/api/v1/admin/analytics", headers=_headers(student))
    assert forbidden.status_code == 403

    login = client.post("/api/v1/auth/login", json={"email": "admin@example.edu", "password": "AdminPassword!123"})
    assert login.status_code == 200
    allowed = client.get("/api/v1/admin/analytics", headers=_headers(login.json()))
    assert allowed.status_code == 200
    body = allowed.json()
    assert body["summary"]["total_students"] == 1
    assert body["summary"]["total_faculty"] == 1
    assert "description" not in str(body)
    assert "password_hash" not in str(body)


def test_admin_management_endpoints_and_audit_log(admin_context) -> None:
    client, factory = admin_context
    with factory() as db:
        admin = User(name="Admin", email="admin@example.edu", password_hash=hash_password("AdminPassword!123"), role="admin")
        student = User(name="Student", email="student@example.edu", password_hash=hash_password("StudentPassword!123"), role="student")
        lesson = CybersecurityLesson(title="Phishing", description="Learn to pause.", category="phishing", content="Content", difficulty="beginner")
        quiz = Quiz(lesson=lesson, title="Phishing quiz", description="Check knowledge", category="phishing", difficulty="beginner")
        question = QuizQuestion(quiz=quiz, question="Pause?", options=["Yes", "No"], correct_answer="Yes", explanation="Pause before acting.")
        db.add_all([admin, student, lesson, quiz, question])
        db.commit()

    login = client.post("/api/v1/auth/login", json={"email": "admin@example.edu", "password": "AdminPassword!123"})
    headers = _headers(login.json())
    assert client.get("/api/v1/admin/users", headers=headers).json()[1]["email"] == "student@example.edu"
    lessons = client.get("/api/v1/admin/lessons", headers=headers)
    quizzes = client.get("/api/v1/admin/quizzes", headers=headers)
    assert lessons.status_code == 200 and lessons.json()[0]["quiz_count"] == 1
    assert quizzes.status_code == 200 and quizzes.json()[0]["question_count"] == 1

    updated = client.patch("/api/v1/admin/users/2", headers=headers, json={"role": "faculty"})
    assert updated.status_code == 200
    assert updated.json()["role"] == "faculty"
    with factory() as db:
        assert db.query(AuditLog).filter_by(action="update_user", entity_id=2).count() == 1
