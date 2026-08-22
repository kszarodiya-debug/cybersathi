"""FastAPI dependencies for authenticated users and role guards."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.auth.tokens import AuthenticationConfigurationError, decode_access_token
from app.core.config import settings
from app.db.session import get_db
from app.models.revoked_token import RevokedToken
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login",
)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Decode a bearer token and load the current user from the database."""

    try:
        payload = decode_access_token(token)
    except AuthenticationConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured.",
        ) from None
    except InvalidTokenError:
        raise _unauthorized() from None

    jti = payload["jti"]
    if db.get(RevokedToken, jti) is not None:
        raise _unauthorized()

    user_id = int(payload["sub"])
    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def _require_student(current_user: CurrentUser) -> User:
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )
    return current_user


StudentOnlyAccess = Annotated[User, Depends(_require_student)]


def require_roles(*allowed_roles: str):
    """Build a dependency that authorizes only the supplied current-user roles."""

    def role_dependency(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return current_user

    return role_dependency


def require_admin(current_user: CurrentUser) -> User:
    """Authorize an administrator using the database-backed role."""

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )
    return current_user


AdminAccess = Annotated[User, Depends(require_admin)]
