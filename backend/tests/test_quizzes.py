from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.rate_limit import auth_rate_limiter
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.awareness import AwarenessScore
from app.models.lesson import CybersecurityLesson, Quiz, QuizQuestion
from app.models.quiz_attempt import QuizAttempt
from app.models.revoked_token import RevokedToken
from app.models.user import User


@pytest.fixture
def quiz_context(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(settings, "jwt_secret", "test-only-quizzes-secret-not-production")
    auth_rate_limiter.reset()
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    original_options_type = QuizQuestion.__table__.c.options.type
    # The application model intentionally uses PostgreSQL JSONB. Use SQLite JSON
    # only for this isolated unit-test database, without changing production code.
    QuizQuestion.__table__.c.options.type = JSON()
    try:
        for table in (
            User.__table__,
            CybersecurityLesson.__table__,
            Quiz.__table__,
            QuizQuestion.__table__,
            QuizAttempt.__table__,
            AwarenessScore.__table__,
            RevokedToken.__table__,
        ):
            table.create(test_engine)
    except Exception:
        QuizQuestion.__table__.c.options.type = original_options_type
        raise
    test_session_factory = sessionmaker(bind=test_engine, expire_on_commit=False)

    with test_session_factory() as db:
        phishing_lesson = CybersecurityLesson(
            title="Phishing basics",
            description="Recognize suspicious messages.",
            category="phishing",
            content="Pause before you click.",
            difficulty="beginner",
        )
        password_lesson = CybersecurityLesson(
            title="Password basics",
            description="Build safer account habits.",
            category="password-security",
            content="Use unique passphrases.",
            difficulty="beginner",
        )
        phishing_quiz = Quiz(
            lesson=phishing_lesson,
            title="Phishing Check",
            description="Test phishing awareness.",
            category="phishing",
            difficulty="beginner",
        )
        password_quiz = Quiz(
            lesson=password_lesson,
            title="Password Check",
            description="Test password awareness.",
            category="password-security",
            difficulty="beginner",
        )
        phishing_quiz.questions = [
            QuizQuestion(
                question="What should you do with an urgent login link?",
                options=["Click it", "Verify separately"],
                correct_answer="Verify separately",
                explanation="Verify unexpected requests through a trusted channel.",
            ),
            QuizQuestion(
                question="Should you share an OTP by message?",
                options=["Yes", "No"],
                correct_answer="No",
                explanation="One-time codes are authentication secrets.",
            ),
        ]
        password_quiz.questions = [
            QuizQuestion(
                question="What is safer?",
                options=["Unique passphrases", "Reused passwords"],
                correct_answer="Unique passphrases",
                explanation="Unique passphrases limit breach impact.",
            ),
            QuizQuestion(
                question="What should protect important accounts?",
                options=["MFA", "A public password"],
                correct_answer="MFA",
                explanation="MFA adds another proof of identity.",
            ),
        ]
        db.add_all([phishing_lesson, password_lesson, phishing_quiz, password_quiz])
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
        QuizQuestion.__table__.c.options.type = original_options_type
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


def _headers(session: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['access_token']}"}


def _quiz_id(client: TestClient, headers: dict[str, str], title: str = "Phishing Check") -> int:
    response = client.get("/api/v1/students/quizzes", headers=headers)
    assert response.status_code == 200
    quiz = next(item for item in response.json()["quizzes"] if item["title"] == title)
    return quiz["id"]


def _start(client: TestClient, headers: dict[str, str], quiz_id: int) -> dict:
    response = client.post(f"/api/v1/students/quizzes/{quiz_id}/attempts", headers=headers)
    assert response.status_code == 201
    return response.json()


def test_quiz_requires_authentication_and_hides_correct_answers(quiz_context) -> None:
    client, _ = quiz_context
    assert client.get("/api/v1/students/quizzes").status_code == 401

    session = _register(client, "catalog@example.edu")
    response = client.get("/api/v1/students/quizzes", headers=_headers(session))
    assert response.status_code == 200
    assert response.json()["categories"] == ["password-security", "phishing"]

    detail = client.get(
        f"/api/v1/students/quizzes/{_quiz_id(client, _headers(session))}",
        headers=_headers(session),
    )
    assert detail.status_code == 200
    assert all("correct_answer" not in question for question in detail.json()["questions"])


def test_correct_answers_are_graded_by_backend_and_duplicate_submit_is_rejected(quiz_context) -> None:
    client, session_factory = quiz_context
    session = _register(client, "correct@example.edu")
    headers = _headers(session)
    attempt = _start(client, headers, _quiz_id(client, headers))

    response = client.post(
        f"/api/v1/students/quizzes/{attempt['quiz_id']}/attempts/{attempt['attempt_id']}/submit",
        headers=headers,
        json={
            "answers": [
                {"question_id": attempt["questions"][0]["id"], "answer": "Verify separately"},
                {"question_id": attempt["questions"][1]["id"], "answer": "No"},
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["score"] == 100.0
    assert all(row["is_correct"] for row in response.json()["results"])
    assert response.json()["awareness_score"]["phishing_score"] == 100.0

    duplicate = client.post(
        f"/api/v1/students/quizzes/{attempt['quiz_id']}/attempts/{attempt['attempt_id']}/submit",
        headers=headers,
        json={"answers": []},
    )
    assert duplicate.status_code == 422  # Payload validation occurs before submitted-state handling.

    with session_factory() as db:
        stored = db.query(QuizAttempt).filter_by(id=attempt["attempt_id"]).one()
        assert stored.status == "submitted"
        assert stored.score == 100

    duplicate_valid = client.post(
        f"/api/v1/students/quizzes/{attempt['quiz_id']}/attempts/{attempt['attempt_id']}/submit",
        headers=headers,
        json={
            "answers": [
                {"question_id": attempt["questions"][0]["id"], "answer": "Verify separately"},
                {"question_id": attempt["questions"][1]["id"], "answer": "No"},
            ],
        },
    )
    assert duplicate_valid.status_code == 409


def test_incorrect_answers_return_explanations_and_calculate_category_scores(quiz_context) -> None:
    client, _ = quiz_context
    session = _register(client, "scores@example.edu")
    headers = _headers(session)
    phishing = _start(client, headers, _quiz_id(client, headers))
    phishing_result = client.post(
        f"/api/v1/students/quizzes/{phishing['quiz_id']}/attempts/{phishing['attempt_id']}/submit",
        headers=headers,
        json={
            "answers": [
                {"question_id": phishing["questions"][0]["id"], "answer": "Click it"},
                {"question_id": phishing["questions"][1]["id"], "answer": "No"},
            ],
        },
    )
    assert phishing_result.status_code == 200
    assert phishing_result.json()["score"] == 50.0
    assert phishing_result.json()["results"][0]["is_correct"] is False
    assert phishing_result.json()["results"][0]["explanation"]

    password = _start(client, headers, _quiz_id(client, headers, "Password Check"))
    password_result = client.post(
        f"/api/v1/students/quizzes/{password['quiz_id']}/attempts/{password['attempt_id']}/submit",
        headers=headers,
        json={
            "answers": [
                {"question_id": password["questions"][0]["id"], "answer": "Unique passphrases"},
                {"question_id": password["questions"][1]["id"], "answer": "A public password"},
            ],
        },
    )
    assert password_result.status_code == 200
    awareness = password_result.json()["awareness_score"]
    assert awareness["phishing_score"] == 50.0
    assert awareness["password_score"] == 50.0
    assert awareness["overall_score"] == 50.0
    assert awareness["mobile_score"] == 0.0


def test_attempt_is_user_scoped_and_answers_are_validated(quiz_context) -> None:
    client, _ = quiz_context
    owner = _register(client, "owner@example.edu")
    other_user = _register(client, "other@example.edu")
    owner_headers = _headers(owner)
    other_headers = _headers(other_user)
    attempt = _start(client, owner_headers, _quiz_id(client, owner_headers))

    unauthorized_submit = client.post(
        f"/api/v1/students/quizzes/{attempt['quiz_id']}/attempts/{attempt['attempt_id']}/submit",
        headers=other_headers,
        json={
            "answers": [
                {"question_id": attempt["questions"][0]["id"], "answer": "Verify separately"},
                {"question_id": attempt["questions"][1]["id"], "answer": "No"},
            ],
        },
    )
    assert unauthorized_submit.status_code == 404

    invalid = client.post(
        f"/api/v1/students/quizzes/{attempt['quiz_id']}/attempts/{attempt['attempt_id']}/submit",
        headers=owner_headers,
        json={
            "answers": [
                {"question_id": attempt["questions"][0]["id"], "answer": "Not an option"},
                {"question_id": attempt["questions"][0]["id"], "answer": "Verify separately"},
            ],
        },
    )
    assert invalid.status_code == 422

    history = client.get("/api/v1/students/quiz-attempts", headers=owner_headers)
    assert history.status_code == 200
    assert history.json()["attempts"] == []
