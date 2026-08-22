"""One-time, environment-backed provisioning for the designated administrator."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User


class AdminBootstrapError(RuntimeError):
    """Raised when administrator provisioning cannot safely proceed."""


def bootstrap_admin_account(
    db: Session,
    *,
    email: str | None = None,
    initial_password: str | None = None,
) -> User:
    """Create the configured admin once without resetting an existing password.

    The function deliberately refuses to promote an existing non-admin account.
    Any role change must be an explicit, authenticated administrative action.
    """

    configured_email = (email or (str(settings.admin_email) if settings.admin_email else "")).strip().lower()
    configured_password = initial_password
    if configured_password is None and settings.admin_initial_password is not None:
        configured_password = settings.admin_initial_password.get_secret_value()
    if not configured_email or not configured_password:
        raise AdminBootstrapError("ADMIN_EMAIL and ADMIN_INITIAL_PASSWORD must be configured for bootstrap.")
    if len(configured_password) < 16:
        raise AdminBootstrapError("ADMIN_INITIAL_PASSWORD must be at least 16 characters long.")

    user = db.scalar(select(User).where(User.email == configured_email))
    if user is not None:
        if user.role != "admin":
            raise AdminBootstrapError(
                "The configured admin email belongs to a non-admin account; no changes were made."
            )
        return user

    user = User(
        name="CyberSathi Administrator",
        email=configured_email,
        password_hash=hash_password(configured_password),
        role="admin",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise AdminBootstrapError("The administrator account could not be created safely.") from error
    db.refresh(user)
    return user


def main() -> None:
    """Provision the account using ADMIN_EMAIL and ADMIN_INITIAL_PASSWORD."""

    with SessionLocal() as db:
        user = bootstrap_admin_account(db)
    print(f"Administrator bootstrap complete for {user.email}.")


if __name__ == "__main__":
    main()
