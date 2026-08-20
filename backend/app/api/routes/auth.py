"""Registration, login, logout, and current-user routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, oauth2_scheme
from app.auth.passwords import hash_password, verify_password
from app.auth.rate_limit import login_identity_rate_limit, login_rate_limit, registration_rate_limit
from app.auth.tokens import AuthenticationConfigurationError, create_access_token, decode_access_token
from app.db.session import get_db
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutResponse, RegisterRequest, TokenResponse, UserResponse


router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _token_response(user: User) -> TokenResponse:
    try:
        access_token, expires_in = create_access_token(user_id=user.id, role=user.role)
    except AuthenticationConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured.",
        ) from None
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(registration_rate_limit)],
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Create a student account; elevated roles are provisioned separately."""

    normalized_email = _normalize_email(str(payload.email))
    if db.scalar(select(User).where(User.email == normalized_email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        name=payload.name,
        email=normalized_email,
        password_hash=hash_password(payload.password.get_secret_value()),
        department=payload.department,
        year=payload.year,
        role="student",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from None
    db.refresh(user)
    return _token_response(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(login_rate_limit)],
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate with a generic error for unknown or incorrect credentials."""

    normalized_email = _normalize_email(str(payload.email))
    login_identity_rate_limit(normalized_email)
    user = db.scalar(select(User).where(User.email == normalized_email))
    password = payload.password.get_secret_value()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _token_response(user)


@router.get("/me", response_model=UserResponse)
def current_user(current_user: CurrentUser) -> User:
    """Return the authenticated user without sensitive credential fields."""

    return current_user


@router.post("/logout", response_model=LogoutResponse)
def logout(
    current_user: CurrentUser,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    """Revoke the current token until its natural expiry and clear client state."""

    del current_user  # The dependency validates that this is the current user.
    try:
        payload = decode_access_token(token)
    except AuthenticationConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured.",
        ) from None
    jti = str(payload["jti"])
    if db.get(RevokedToken, jti) is None:
        expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
        db.add(RevokedToken(jti=jti, expires_at=expires_at))
        db.commit()
    return LogoutResponse(message="Logged out successfully.")
