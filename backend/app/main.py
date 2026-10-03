"""FastAPI application entry point for CyberSathi."""

from contextlib import asynccontextmanager
import logging
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.api.router import api_router
from app.core.config import settings
from app.schemas.health import HealthResponse


logger = logging.getLogger("cybersathi.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Start the API and optionally apply migrations in an explicit release mode."""

    if settings.app_env == "production" and settings.run_migrations_on_startup:
        backend_root = Path(__file__).resolve().parents[1]
        alembic_config = Config(str(backend_root / "alembic.ini"))
        logger.info("Applying database migrations in startup migration mode")
        command.upgrade(alembic_config, "head")
        logger.info("Database migrations completed")
    elif settings.app_env == "production":
        logger.warning(
            "Startup migrations are disabled; run 'alembic upgrade head' as a separate release step."
        )
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend foundation for the CyberSathi awareness platform.",
    lifespan=lifespan,
    docs_url=None if settings.app_env == "production" else "/docs",
    redoc_url=None if settings.app_env == "production" else "/redoc",
    openapi_url=None if settings.app_env == "production" else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Authorization", "Content-Type"],
)


def _add_security_headers(response: Response) -> None:
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'; base-uri 'none'")
    response.headers.setdefault("Cache-Control", "no-store")
    if settings.app_env == "production":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    request_id = str(uuid4())
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request failure request_id=%s path=%s", request_id, request.url.path)
        response = JSONResponse(
            status_code=500,
            content={"detail": "An unexpected server error occurred.", "request_id": request_id},
        )
    _add_security_headers(response)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health_check() -> HealthResponse:
    """Return a lightweight liveness response without requiring a database."""

    return HealthResponse(
        status="ok",
        service="cybersathi-api",
        version=settings.app_version,
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)
