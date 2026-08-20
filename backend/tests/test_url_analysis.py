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
from app.models.analysis import URLAnalysis
from app.models.revoked_token import RevokedToken
from app.models.user import User


@pytest.fixture
def url_context(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(settings, "jwt_secret", "test-only-url-secret-not-production")
    auth_rate_limiter.reset()
    analysis_rate_limiter.reset()
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(test_engine)
    URLAnalysis.__table__.create(test_engine)
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


def test_safe_url_returns_safe_result_without_network_access(url_context) -> None:
    client, session_factory = url_context
    user = _register(client, "safe@example.edu")

    response = client.post(
        "/api/v1/students/analysis/urls",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={"url": "https://portal.example.edu/resources/cybersecurity"},
    )

    assert response.status_code == 201
    result = response.json()
    assert result["risk_score"] == 0
    assert result["risk_level"] == "SAFE"
    assert result["detected_indicators"] == []
    assert "no connection was made" in result["explanation"]
    with session_factory() as db:
        saved = db.query(URLAnalysis).one()
        assert saved.risk_level == "safe"
        assert saved.detected_indicators == []


def test_suspicious_url_returns_structured_high_result(url_context) -> None:
    client, session_factory = url_context
    user = _register(client, "suspicious@example.edu")
    suspicious_url = "http://user:pass@192.168.1.10/login?redirect=https%3A%2F%2Fpaypal.example&token=abc"

    response = client.post(
        "/api/v1/students/analysis/urls",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={"url": suspicious_url},
    )

    assert response.status_code == 201
    result = response.json()
    assert result["risk_score"] >= 60
    assert result["risk_level"] in {"HIGH", "CRITICAL"}
    codes = {indicator["code"] for indicator in result["detected_indicators"]}
    assert {"https_not_used", "embedded_credentials", "ip_address_host", "suspicious_keyword", "suspicious_query"}.issubset(codes)
    assert "no connection was made" in result["explanation"]
    assert result["recommended_action"]
    with session_factory() as db:
        saved = db.query(URLAnalysis).one()
        assert saved.url == suspicious_url
        assert saved.recommended_action == result["recommended_action"]


def test_url_history_is_scoped_and_validation_is_safe(url_context) -> None:
    client, _ = url_context
    primary = _register(client, "primary@example.edu")
    secondary = _register(client, "secondary@example.edu")
    primary_headers = {"Authorization": f"Bearer {primary['access_token']}"}
    secondary_headers = {"Authorization": f"Bearer {secondary['access_token']}"}

    created = client.post(
        "/api/v1/students/analysis/urls",
        headers=primary_headers,
        json={"url": "https://example.edu"},
    )
    assert created.status_code == 201
    assert len(client.get("/api/v1/students/analysis/urls/history", headers=primary_headers).json()) == 1
    assert client.get("/api/v1/students/analysis/urls/history", headers=secondary_headers).json() == []

    invalid = client.post(
        "/api/v1/students/analysis/urls",
        headers=primary_headers,
        json={"url": "javascript:alert(1)"},
    )
    assert invalid.status_code == 422
