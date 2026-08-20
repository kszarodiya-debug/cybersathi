"""Validated schemas for student incident reports and admin workflows."""

from datetime import datetime
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator


IncidentType = Literal[
    "phishing",
    "suspicious_link",
    "account_compromise",
    "cyberbullying",
    "malware",
    "data_leakage",
    "online_scam",
    "fake_website",
    "other",
]
IncidentStatus = Literal["OPEN", "UNDER_REVIEW", "RESOLVED", "REJECTED"]
IncidentSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class IncidentCreateRequest(BaseModel):
    incident_type: IncidentType
    description: str = Field(min_length=10, max_length=10_000)
    suspicious_url: AnyHttpUrl | None = None
    occurred_at: datetime
    evidence_metadata: dict[str, str] = Field(default_factory=dict, max_length=10)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("occurred_at")
    @classmethod
    def validate_occurred_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Date/time must include a timezone.")
        return value

    @field_validator("evidence_metadata")
    @classmethod
    def validate_evidence_metadata(cls, value: dict[str, str]) -> dict[str, str]:
        for key, item in value.items():
            if not key.strip() or "\x00" in key or "\x00" in item:
                raise ValueError("Evidence metadata contains an invalid value.")
            if len(key) > 50 or len(item) > 500:
                raise ValueError("Evidence metadata keys and values must be concise.")
        return value


class IncidentReportResponse(BaseModel):
    id: int
    user_id: int
    incident_type: IncidentType
    description: str
    suspicious_url: str | None
    occurred_at: datetime
    evidence_metadata: dict[str, str]
    status: IncidentStatus
    severity: IncidentSeverity
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentReportListResponse(BaseModel):
    reports: list[IncidentReportResponse]
    total: int


class IncidentAdminReportResponse(IncidentReportResponse):
    reporter_name: str
    reporter_email: str
    reporter_department: str | None


class IncidentAdminReportListResponse(BaseModel):
    reports: list[IncidentAdminReportResponse]
    total: int


class IncidentAdminUpdateRequest(BaseModel):
    status: IncidentStatus | None = None
    severity: IncidentSeverity | None = None

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("status", "severity")
    @classmethod
    def reject_empty_updates(cls, value: str | None) -> str | None:
        return value


class AuditLogResponse(BaseModel):
    id: int
    actor_user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    details: dict[str, str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
