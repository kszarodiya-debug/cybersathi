"""Environment-backed application settings."""

from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import AliasChoices, EmailStr, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="CYBERSATHI API", validation_alias="APP_NAME")
    app_env: Literal["development", "test", "staging", "production"] = Field(
        default="development", validation_alias="APP_ENV"
    )
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    database_url: str = Field(
        default="postgresql+psycopg://localhost/cybersathi",
        validation_alias="DATABASE_URL",
    )
    jwt_secret: str | None = Field(
        default=None,
        min_length=32,
        validation_alias="JWT_SECRET",
    )
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = Field(
        default="HS256", validation_alias="JWT_ALGORITHM"
    )
    jwt_issuer: str = Field(default="cybersathi-api", min_length=3, max_length=100, validation_alias="JWT_ISSUER")
    jwt_audience: str = Field(default="cybersathi-client", min_length=3, max_length=100, validation_alias="JWT_AUDIENCE")
    access_token_expire_minutes: int = Field(
        default=15,
        ge=5,
        le=60,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    auth_rate_limit_window_seconds: int = Field(
        default=60,
        ge=10,
        le=3600,
        validation_alias="AUTH_RATE_LIMIT_WINDOW_SECONDS",
    )
    auth_login_rate_limit: int = Field(
        default=10,
        ge=1,
        le=100,
        validation_alias="AUTH_LOGIN_RATE_LIMIT",
    )
    auth_register_rate_limit: int = Field(
        default=5,
        ge=1,
        le=100,
        validation_alias="AUTH_REGISTER_RATE_LIMIT",
    )
    chat_rate_limit: int = Field(
        default=20,
        ge=1,
        le=200,
        validation_alias="CHAT_RATE_LIMIT",
    )
    analysis_rate_limit: int = Field(
        default=30,
        ge=1,
        le=300,
        validation_alias="ANALYSIS_RATE_LIMIT",
    )
    submission_rate_limit: int = Field(
        default=60,
        ge=1,
        le=300,
        validation_alias="SUBMISSION_RATE_LIMIT",
    )
    ai_provider: str = Field(default="openai_compatible", validation_alias="AI_PROVIDER")
    ai_api_key: str | None = Field(default=None, validation_alias="AI_API_KEY")
    ai_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias="AI_BASE_URL",
    )
    ai_model: str = Field(default="gpt-4o-mini", validation_alias="AI_MODEL")
    ai_timeout_seconds: float = Field(
        default=20.0,
        ge=1.0,
        le=120.0,
        validation_alias="AI_TIMEOUT_SECONDS",
    )
    ai_max_history_messages: int = Field(
        default=10,
        ge=2,
        le=30,
        validation_alias="AI_MAX_HISTORY_MESSAGES",
    )
    frontend_origins_raw: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices("CORS_ORIGINS", "FRONTEND_ORIGINS"),
    )
    admin_email: EmailStr | None = Field(default=None, validation_alias="ADMIN_EMAIL")
    admin_initial_password: SecretStr | None = Field(
        default=None, validation_alias="ADMIN_INITIAL_PASSWORD"
    )

    @property
    def frontend_origins(self) -> list[str]:
        """Return configured CORS origins as a normalized list."""

        return [
            origin.strip()
            for origin in self.frontend_origins_raw.split(",")
            if origin.strip()
        ]

    @field_validator("frontend_origins_raw")
    @classmethod
    def validate_frontend_origins(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if not origins or "*" in origins:
            raise ValueError("FRONTEND_ORIGINS must contain explicit HTTP(S) origins; wildcards are not allowed.")
        for origin in origins:
            parsed = urlsplit(origin)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path not in {"", "/"}:
                raise ValueError("FRONTEND_ORIGINS contains an invalid origin.")
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError("FRONTEND_ORIGINS must not contain credentials, paths, queries, or fragments.")
        return value

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env == "production":
            if not self.jwt_secret:
                raise ValueError("JWT_SECRET must be configured in production.")
            if len(self.jwt_secret) < 32:
                raise ValueError("JWT_SECRET must be at least 32 characters in production.")
            if not self.ai_base_url.startswith("https://"):
                raise ValueError("AI_BASE_URL must use HTTPS in production.")
        if bool(self.admin_email) != bool(self.admin_initial_password):
            raise ValueError("ADMIN_EMAIL and ADMIN_INITIAL_PASSWORD must be configured together.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
