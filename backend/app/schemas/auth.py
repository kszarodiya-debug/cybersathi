"""Authentication request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: SecretStr = Field(min_length=12, max_length=128)
    department: str | None = Field(default=None, min_length=1, max_length=120)
    year: int | None = Field(default=None, gt=0, le=10)


class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    department: str | None
    year: int | None
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class LogoutResponse(BaseModel):
    message: str
