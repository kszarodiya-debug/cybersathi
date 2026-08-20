from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.passwords import hash_password
from app.auth.rate_limit import auth_rate_limiter
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.audit import AuditLog
from app.models.incident import IncidentReport
from app.models.revoked_token import RevokedToken
from app.models.user import User


@pytest.fixture
def incident_context(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(settings, "jwt_secret", "test-only-incidents-secret-not-production")
    auth_rate_limiter.reset()
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    for table in (User.__table__, IncidentReport.__table__, AuditLog.__table__, RevokedToken.__table__):
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


def _headers(session: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['access_token']}"}


def _payload(description: str = "A suspicious message asked for an account code.") -> dict:
    return {
        "incident_type": "phishing",
        "description": description,
        "suspicious_url": "https://example.invalid/login",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "evidence_metadata": {"channel": "email", "sender": "Campus IT"},
    }


def test_students_can_submit_and_only_see_their_own_reports(incident_context) -> None:
    client, _ = incident_context
    first = _register(client, "first@example.edu")
    second = _register(client, "second@example.edu")

    created = client.post("/api/v1/students/incidents", headers=_headers(first), json=_payload())
    assert created.status_code == 201
    report = created.json()
    assert report["status"] == "OPEN"
    assert report["severity"] == "MEDIUM"
    assert report["evidence_metadata"]["channel"] == "email"

    own = client.get("/api/v1/students/incidents", headers=_headers(first))
    other = client.get("/api/v1/students/incidents", headers=_headers(second))
    assert own.json()["total"] == 1
    assert other.json()["total"] == 0

    hidden = client.get(f"/api/v1/students/incidents/{report['id']}", headers=_headers(second))
    assert hidden.status_code == 404


def test_report_input_is_validated_and_student_cannot_choose_severity(incident_context) -> None:
    client, _ = incident_context
    session = _register(client, "validation@example.edu")
    payload = _payload("short")
    payload["severity"] = "CRITICAL"
    invalid = client.post("/api/v1/students/incidents", headers=_headers(session), json=payload)
    assert invalid.status_code == 422


def test_only_admin_can_manage_reports_and_admin_actions_are_audited(incident_context) -> None:
    client, session_factory = incident_context
    student = _register(client, "student@example.edu")
    created = client.post("/api/v1/students/incidents", headers=_headers(student), json=_payload())
    report_id = created.json()["id"]

    forbidden = client.get("/api/v1/admin/incidents", headers=_headers(student))
    assert forbidden.status_code == 403

    with session_factory() as db:
        admin = User(
            name="Platform Admin",
            email="admin@example.edu",
            password_hash=hash_password("AdminPassword!123"),
            role="admin",
        )
        db.add(admin)
        db.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.edu", "password": "AdminPassword!123"},
    )
    assert login.status_code == 200
    admin_headers = _headers(login.json())

    queue = client.get("/api/v1/admin/incidents", headers=admin_headers)
    assert queue.status_code == 200
    assert queue.json()["reports"][0]["reporter_email"] == "student@example.edu"

    update = client.patch(
        f"/api/v1/admin/incidents/{report_id}",
        headers=admin_headers,
        json={"status": "UNDER_REVIEW", "severity": "HIGH"},
    )
    assert update.status_code == 200
    assert update.json()["status"] == "UNDER_REVIEW"
    assert update.json()["severity"] == "HIGH"

    with session_factory() as db:
        audit = db.query(AuditLog).one()
        assert audit.action == "INCIDENT_REPORT_UPDATED"
        assert audit.actor_user_id is not None
        assert audit.details["status_to"] == "UNDER_REVIEW"
        assert audit.details["severity_to"] == "HIGH"


def test_non_admin_cannot_update_a_report(incident_context) -> None:
    client, _ = incident_context
    student = _register(client, "student2@example.edu")
    created = client.post("/api/v1/students/incidents", headers=_headers(student), json=_payload())
    response = client.patch(
        f"/api/v1/admin/incidents/{created.json()['id']}",
        headers=_headers(student),
        json={"status": "RESOLVED"},
    )
    assert response.status_code == 403
