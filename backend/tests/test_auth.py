from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.passwords import hash_password, verify_password
from app.auth.rate_limit import auth_rate_limiter
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.revoked_token import RevokedToken
from app.models.user import User


@pytest.fixture
def auth_context(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setattr(settings, "jwt_secret", "test-only-jwt-secret-not-used-in-production")
    auth_rate_limiter.reset()
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(test_engine)
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
        app.dependency_overrides.clear()
        test_engine.dispose()


def _register(client: TestClient, email: str = "student@example.edu") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Campus Student",
            "email": email,
            "password": "StrongPassword!123",
            "department": "Computer Science",
            "year": 2,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_registration_hashes_password_and_hides_hash(auth_context) -> None:
    client, session_factory = auth_context

    result = _register(client)

    assert result["user"]["email"] == "student@example.edu"
    assert "password_hash" not in result["user"]
    with session_factory() as db:
        user = db.query(User).filter_by(email="student@example.edu").one()
        assert user.password_hash != "StrongPassword!123"
        assert user.password_hash.startswith("$argon2id$")
        assert verify_password("StrongPassword!123", user.password_hash)


def test_login_returns_access_token(auth_context) -> None:
    client, _ = auth_context
    _register(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "STUDENT@example.edu", "password": "StrongPassword!123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]
    assert "password_hash" not in response.json()["user"]


def test_invalid_credentials_are_rejected_generically(auth_context) -> None:
    client, _ = auth_context
    _register(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@example.edu", "password": "WrongPassword!123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."
    assert response.headers["www-authenticate"] == "Bearer"


def test_protected_endpoint_requires_authentication(auth_context) -> None:
    client, _ = auth_context

    unauthenticated = client.get("/api/v1/lessons")
    assert unauthenticated.status_code == 401

    result = _register(client)
    authenticated = client.get(
        "/api/v1/lessons",
        headers={"Authorization": f"Bearer {result['access_token']}"},
    )
    assert authenticated.status_code == 200
    assert authenticated.json()["feature"] == "lessons"


def test_role_authorization_blocks_student_and_allows_admin(auth_context) -> None:
    client, session_factory = auth_context
    student = _register(client)

    forbidden = client.get(
        "/api/v1/admin/analytics",
        headers={"Authorization": f"Bearer {student['access_token']}"},
    )
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

    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.edu", "password": "AdminPassword!123"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    allowed = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert allowed.status_code == 200
    assert all("password_hash" not in user for user in allowed.json())


def test_logout_revokes_the_access_token(auth_context) -> None:
    client, _ = auth_context
    result = _register(client)
    headers = {"Authorization": f"Bearer {result['access_token']}"}

    logout = client.post("/api/v1/auth/logout", headers=headers)
    assert logout.status_code == 200

    after_logout = client.get("/api/v1/auth/me", headers=headers)
    assert after_logout.status_code == 401
