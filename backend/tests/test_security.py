from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from jwt import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.rate_limit import auth_rate_limiter, submission_rate_limiter
from app.auth.tokens import create_access_token, decode_access_token
from app.core.config import Settings, settings
from app.db.session import get_db
from app.main import app
from app.models.revoked_token import RevokedToken
from app.models.user import User


@pytest.fixture
def security_context(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(settings, "jwt_secret", "test-only-security-secret-not-production")
    auth_rate_limiter.reset()
    submission_rate_limiter.reset()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    User.__table__.create(engine)
    RevokedToken.__table__.create(engine)
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
        submission_rate_limiter.reset()
        app.dependency_overrides.clear()
        engine.dispose()


def test_security_headers_and_cors_are_explicit(security_context) -> None:
    client, _ = security_context
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Content-Security-Policy"].startswith("default-src 'none'")
    assert response.headers["X-Request-ID"]
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-credentials" not in response.headers

    wildcard = client.get("/health", headers={"Origin": "https://attacker.example"})
    assert "access-control-allow-origin" not in wildcard.headers


def test_settings_reject_wildcard_origins_and_insecure_production() -> None:
    with pytest.raises(ValidationError):
        Settings(FRONTEND_ORIGINS="*")
    assert Settings(CORS_ORIGINS="https://campus.example").frontend_origins == ["https://campus.example"]
    with pytest.raises(ValidationError):
        Settings(APP_ENV="production", FRONTEND_ORIGINS="https://campus.example", AI_BASE_URL="http://ai.example")


def test_jwt_requires_configured_audience_and_issuer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "jwt_secret", "test-only-jwt-security-secret-32-bytes")
    token, _ = create_access_token(user_id=7, role="student")
    assert decode_access_token(token)["sub"] == "7"

    monkeypatch.setattr(settings, "jwt_audience", "different-client")
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_faculty_cannot_use_student_private_apis(security_context) -> None:
    client, factory = security_context
    registered = client.post(
        "/api/v1/auth/register",
        json={"name": "Faculty", "email": "faculty@example.edu", "password": "StrongPassword!123"},
    )
    assert registered.status_code == 201
    with factory() as db:
        user = db.query(User).filter_by(email="faculty@example.edu").one()
        user.role = "faculty"
        db.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "faculty@example.edu", "password": "StrongPassword!123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    for path in ("/api/v1/chat/history", "/api/v1/students/lessons", "/api/v1/students/quizzes", "/api/v1/students/analysis/urls/history"):
        assert client.get(path, headers=headers).status_code == 403
