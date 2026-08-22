from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.passwords import verify_password
from app.bootstrap_admin import AdminBootstrapError, bootstrap_admin_account
from app.models.user import User


def _db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    User.__table__.create(engine)
    return Session(engine)


def test_bootstrap_creates_one_hashed_admin_and_is_idempotent() -> None:
    db = _db()
    try:
        admin = bootstrap_admin_account(
            db,
            email="owner@example.edu",
            initial_password="A-unique-bootstrap-password-123",
        )
        original_hash = admin.password_hash
        assert admin.role == "admin"
        assert verify_password("A-unique-bootstrap-password-123", original_hash)

        same_admin = bootstrap_admin_account(
            db,
            email="owner@example.edu",
            initial_password="A-different-password-that-is-not-used",
        )
        assert same_admin.id == admin.id
        assert same_admin.password_hash == original_hash
        assert db.query(User).filter_by(role="admin").count() == 1
    finally:
        db.close()


def test_bootstrap_refuses_to_promote_existing_normal_account() -> None:
    db = _db()
    try:
        db.add(User(name="Student", email="owner@example.edu", password_hash="existing-hash", role="student"))
        db.commit()
        try:
            bootstrap_admin_account(db, email="owner@example.edu", initial_password="A-unique-bootstrap-password-123")
        except AdminBootstrapError as error:
            assert "non-admin" in str(error)
        else:
            raise AssertionError("Expected bootstrap to refuse promotion")
        assert db.query(User).filter_by(role="admin").count() == 0
    finally:
        db.close()
