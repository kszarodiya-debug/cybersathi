"""Small per-process rate limiters for abuse-prone API operations."""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status

from app.core.config import settings


class InMemoryRateLimiter:
    """Sliding-window limiter suitable for a single API process.

    Deployments with multiple workers should move this state to a shared store
    such as Redis; the endpoint limits and API behavior remain the same.
    """

    def __init__(self) -> None:
        self._events: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> int | None:
        """Return retry seconds when limited, otherwise record the attempt."""

        now = monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                return max(1, int(events[0] + window_seconds - now))
            events.append(now)
            return None

    def reset(self) -> None:
        """Clear limiter state, primarily for isolated test/application lifecycle use."""

        with self._lock:
            self._events.clear()


auth_rate_limiter = InMemoryRateLimiter()


def _rate_limit(
    request: Request,
    *,
    limiter: InMemoryRateLimiter,
    action: str,
    limit: int,
    detail: str,
) -> None:
    client_host = request.client.host if request.client else "unknown"
    key = f"{action}:{client_host}"
    retry_after = limiter.check(
        key,
        limit=limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)},
        )


def registration_rate_limit(request: Request) -> None:
    _rate_limit(
        request,
        limiter=auth_rate_limiter,
        action="register",
        limit=settings.auth_register_rate_limit,
        detail="Too many registration attempts. Try again later.",
    )


def login_rate_limit(request: Request) -> None:
    _rate_limit(
        request,
        limiter=auth_rate_limiter,
        action="login",
        limit=settings.auth_login_rate_limit,
        detail="Too many authentication attempts. Try again later.",
    )


def login_identity_rate_limit(email: str) -> None:
    """Add an email-keyed login throttle to resist distributed password spraying."""

    retry_after = auth_rate_limiter.check(
        f"login-email:{email.lower()}",
        limit=settings.auth_login_rate_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )


chat_rate_limiter = InMemoryRateLimiter()


def chat_rate_limit(request: Request) -> None:
    """Limit assistant requests per client address in this API process."""

    _rate_limit(
        request,
        limiter=chat_rate_limiter,
        action="chat",
        limit=settings.chat_rate_limit,
        detail="Too many assistant requests. Please try again later.",
    )


analysis_rate_limiter = InMemoryRateLimiter()


def analysis_rate_limit(request: Request) -> None:
    """Limit message analysis requests per client address in this API process."""

    _rate_limit(
        request,
        limiter=analysis_rate_limiter,
        action="analysis",
        limit=settings.analysis_rate_limit,
        detail="Too many analysis requests. Please try again later.",
    )


submission_rate_limiter = InMemoryRateLimiter()


def submission_rate_limit(request: Request) -> None:
    """Limit state-changing learning and incident submissions per client address."""

    _rate_limit(
        request,
        limiter=submission_rate_limiter,
        action="submission",
        limit=settings.submission_rate_limit,
        detail="Too many submissions. Please try again later.",
    )
