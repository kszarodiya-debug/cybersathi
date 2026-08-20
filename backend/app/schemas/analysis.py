"""Request and response schemas for defensive message analysis."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


MessageContentType = Literal["email", "sms", "whatsapp", "social_media"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
IndicatorSeverity = Literal["low", "medium", "high"]


class MessageAnalysisRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    content_type: MessageContentType = "email"
    message: str = Field(min_length=1, max_length=20_000)

    @field_validator("message")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("Message contains an invalid character.")
        return value


class DetectedIndicator(BaseModel):
    code: str
    label: str
    description: str
    severity: IndicatorSeverity


class MessageAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content_type: MessageContentType
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    detected_indicators: list[DetectedIndicator]
    explanation: str
    recommended_actions: list[str]
    safe_handling_advice: str
    created_at: datetime
