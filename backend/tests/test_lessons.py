from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.rate_limit import auth_rate_limiter
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.lesson import CybersecurityLesson
from app.models.progress import LessonProgress
from app.models.revoked_token import RevokedToken
from app.models.user import User


@pytest.fixture
def lesson_context(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(settings, "jwt_secret", "test-only-lessons-secret-not-production")
    auth_rate_limiter.reset()
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(test_engine)
    CybersecurityLesson.__table__.create(test_engine)
    LessonProgress.__table__.create(test_engine)
    RevokedToken.__table__.create(test_engine)
    test_session_factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    with test_session_factory() as db:
        db.add_all(
            [
                CybersecurityLesson(
                    title="Password foundations",
                    description="Build stronger account habits.",
                    introduction="Passwords protect access to important services.",
                    category="password-security",
                    content="Use unique, long passwords.",
                    learning_objectives=["Identify password reuse risk."],
                    explanation="Unique passwords limit breach impact.",
                    real_world_example="A reused password is tried against campus email.",
                    safety_tips=["Use a password manager."],
                    key_takeaways=["Use unique passwords."],
                    difficulty="beginner",
                ),
                CybersecurityLesson(
                    title="Phishing basics",
                    description="Pause before you click.",
                    introduction="Phishing messages create pressure.",
                    category="phishing",
                    content="Verify unexpected requests.",
                    learning_objectives=["Spot urgency."],
                    explanation="Use trusted channels.",
                    real_world_example="A fake campus message requests a login.",
                    safety_tips=["Report suspicious messages."],
                    key_takeaways=["Verify first."],
                    difficulty="beginner",
                ),
            ]
        )
        db.commit()

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
        json={"name": "Campus Student", "email": email, "password": "StrongPassword!123"},
    )
    assert response.status_code == 201
    return response.json()


def test_learning_hub_lists_database_content_and_filters_categories(lesson_context) -> None:
    client, _ = lesson_context
    user = _register(client, "student@example.edu")
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    all_lessons = client.get("/api/v1/students/lessons", headers=headers)
    filtered = client.get(
        "/api/v1/students/lessons?category=phishing",
        headers=headers,
    )

    assert all_lessons.status_code == 200
    assert all_lessons.json()["total"] == 2
    assert all_lessons.json()["categories"] == ["password-security", "phishing"]
    assert all_lessons.json()["completed_count"] == 0
    assert filtered.json()["total"] == 1
    assert filtered.json()["lessons"][0]["title"] == "Phishing basics"


def test_lesson_detail_and_completion_are_user_scoped(lesson_context) -> None:
    client, session_factory = lesson_context
    primary = _register(client, "primary@example.edu")
    secondary = _register(client, "secondary@example.edu")
    primary_headers = {"Authorization": f"Bearer {primary['access_token']}"}
    secondary_headers = {"Authorization": f"Bearer {secondary['access_token']}"}

    with session_factory() as db:
        lesson_id = db.query(CybersecurityLesson).filter_by(category="password-security").one().id

    detail = client.get(f"/api/v1/students/lessons/{lesson_id}", headers=primary_headers)
    assert detail.status_code == 200
    assert detail.json()["learning_objectives"]
    assert detail.json()["safety_tips"]
    assert detail.json()["completed"] is False

    completed = client.post(
        f"/api/v1/students/lessons/{lesson_id}/complete",
        headers=primary_headers,
    )
    assert completed.status_code == 200
    assert completed.json()["completed"] is True

    primary_list = client.get("/api/v1/students/lessons", headers=primary_headers)
    secondary_detail = client.get(
        f"/api/v1/students/lessons/{lesson_id}", headers=secondary_headers
    )
    assert primary_list.json()["completed_count"] == 1
    assert secondary_detail.json()["completed"] is False


def test_missing_lesson_returns_not_found(lesson_context) -> None:
    client, _ = lesson_context
    user = _register(client, "missing@example.edu")
    response = client.get(
        "/api/v1/students/lessons/9999",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )
    assert response.status_code == 404
