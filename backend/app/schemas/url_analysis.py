"""Request and response schemas for defensive URL analysis."""

from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


URLRiskLevel = Literal["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
URLIndicatorSeverity = Literal["low", "medium", "high"]


class URLAnalysisRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    url: str = Field(min_length=4, max_length=2048)

    @field_validator("url")
    @classmethod
    def validate_http_url(cls, value: str) -> str:
        if "\x00" in value or any(ord(character) < 32 for character in value):
            raise ValueError("URL contains an invalid control character.")
        try:
            parsed = urlsplit(value)
            hostname = parsed.hostname
            parsed.port
        except ValueError as exc:
            raise ValueError("Enter a valid HTTP or HTTPS URL.") from exc
        if parsed.scheme.lower() not in {"http", "https"} or not hostname:
            raise ValueError("Enter a valid HTTP or HTTPS URL.")
        return value


class URLDetectedIndicator(BaseModel):
    code: str
    label: str
    description: str
    severity: URLIndicatorSeverity


class URLAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None
    url: str
    risk_score: int = Field(ge=0, le=100)
    risk_level: URLRiskLevel
    detected_indicators: list[URLDetectedIndicator]
    explanation: str
    recommended_action: str
    created_at: datetime
