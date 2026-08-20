"""JWT access-token creation and decoding."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from jwt import InvalidTokenError

from app.core.config import settings


class AuthenticationConfigurationError(RuntimeError):
    """Raised when the service cannot safely issue or validate access tokens."""


def _jwt_secret() -> str:
    if not settings.jwt_secret:
        raise AuthenticationConfigurationError("JWT_SECRET is not configured")
    return settings.jwt_secret


def create_access_token(*, user_id: int, role: str) -> tuple[str, int]:
    """Create a short-lived JWT access token and return its lifetime in seconds."""

    expires_in = settings.access_token_expire_minutes * 60
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=expires_in)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "jti": str(uuid4()),
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, _jwt_secret(), algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str) -> dict[str, object]:
    """Decode and validate an access token using the configured algorithm."""

    payload = jwt.decode(
        token,
        _jwt_secret(),
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        options={"require": ["sub", "type", "jti", "iat", "exp", "iss", "aud"]},
    )
    if payload.get("type") != "access":
        raise InvalidTokenError("Invalid token type")
    if not isinstance(payload.get("sub"), str) or not payload["sub"].isdigit():
        raise InvalidTokenError("Invalid token subject")
    if not isinstance(payload.get("jti"), str):
        raise InvalidTokenError("Invalid token identifier")
    return payload
