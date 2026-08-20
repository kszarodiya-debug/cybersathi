from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.rate_limit import analysis_rate_limiter, auth_rate_limiter
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.analysis import EmailAnalysis
from app.models.revoked_token import RevokedToken
from app.models.user import User


@pytest.fixture
def analysis_context(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(settings, "jwt_secret", "test-only-analysis-secret-not-production")
    auth_rate_limiter.reset()
    analysis_rate_limiter.reset()
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(test_engine)
    EmailAnalysis.__table__.create(test_engine)
    RevokedToken.__table__.create(test_engine)
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
        analysis_rate_limiter.reset()
        app.dependency_overrides.clear()
        test_engine.dispose()


def _register(client: TestClient, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Campus Student", "email": email, "password": "StrongPassword!123"},
    )
    assert response.status_code == 201
    return response.json()


def test_message_analyzer_returns_structured_critical_result_and_persists_it(analysis_context) -> None:
    client, session_factory = analysis_context
    user = _register(client, "student@example.edu")
    message = """From: IT Support <support@gmail.com>
Reply-To: security@attacker.example
URGENT: your account will be suspended. Click https://bit.ly/verify now and send your password and OTP.
Buy gift cards for an emergency payment. Keep this secret. Open the attached invoice.exe."""

    response = client.post(
        "/api/v1/students/analysis/messages",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={"content_type": "email", "message": message},
    )

    assert response.status_code == 201
    result = response.json()
    assert result["risk_score"] == 100
    assert result["risk_level"] == "CRITICAL"
    codes = {indicator["code"] for indicator in result["detected_indicators"]}
    assert {
        "urgency",
        "impersonation",
        "credential_request",
        "suspicious_link",
        "financial_scam",
        "social_engineering",
        "suspicious_attachment",
        "otp_request",
        "password_request",
        "payment_request",
        "unusual_sender",
    }.issubset(codes)
    assert "not proof" in result["explanation"]
    assert result["recommended_actions"]
    assert result["safe_handling_advice"]

    with session_factory() as db:
        saved = db.query(EmailAnalysis).one()
        assert saved.user_id == user["user"]["id"]
        assert saved.content_type == "email"
        assert len(saved.detected_indicators) >= 10
        assert saved.recommended_actions
        assert saved.analysis_result == result["explanation"]


def test_benign_message_is_low_but_not_declared_safe(analysis_context) -> None:
    client, _ = analysis_context
    user = _register(client, "student@example.edu")

    response = client.post(
        "/api/v1/students/analysis/messages",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={"content_type": "whatsapp", "message": "Hi, are we still meeting at the library at 4 PM?"},
    )

    assert response.status_code == 201
    result = response.json()
    assert result["risk_score"] == 0
    assert result["risk_level"] == "LOW"
    assert result["detected_indicators"] == []
    assert "not proof" in result["explanation"]


def test_message_analyzer_validates_input_and_requires_authentication(analysis_context) -> None:
    client, _ = analysis_context
    unauthenticated = client.post(
        "/api/v1/students/analysis/messages",
        json={"content_type": "sms", "message": "What is this?"},
    )
    assert unauthenticated.status_code == 401

    user = _register(client, "validation@example.edu")
    headers = {"Authorization": f"Bearer {user['access_token']}"}
    blank = client.post(
        "/api/v1/students/analysis/messages",
        headers=headers,
        json={"content_type": "sms", "message": "   "},
    )
    unsupported = client.post(
        "/api/v1/students/analysis/messages",
        headers=headers,
        json={"content_type": "telegram", "message": "Hello"},
    )
    assert blank.status_code == 422
    assert unsupported.status_code == 422
