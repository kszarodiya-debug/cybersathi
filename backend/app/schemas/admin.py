"""Schemas for administrator-only analytics and management views."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AdminUserUpdateRequest(BaseModel):
    """Fields an administrator may change without touching credentials."""

    model_config = ConfigDict(str_strip_whitespace=True)

    role: Literal["student", "faculty", "admin"] | None = None
    department: str | None = Field(default=None, min_length=1, max_length=120)
    year: int | None = Field(default=None, gt=0, le=10)


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    department: str | None
    year: int | None
    created_at: datetime
    updated_at: datetime


class AdminLessonSummary(BaseModel):
    id: int
    title: str
    category: str
    difficulty: str
    quiz_count: int
    created_at: datetime


class AdminQuizSummary(BaseModel):
    id: int
    lesson_id: int
    title: str
    category: str
    difficulty: str
    question_count: int
    attempt_count: int


class AdminMetricSummary(BaseModel):
    total_students: int
    total_faculty: int
    total_users: int
    awareness_average: float
    total_incidents: int
    open_incidents: int
    high_critical_incidents: int
    total_email_analyses: int
    total_url_analyses: int
    quiz_participation: int


class AdminIncidentTrendPoint(BaseModel):
    label: str
    count: int


class AdminCategoryPoint(BaseModel):
    label: str
    count: int


class AdminAwarenessPoint(BaseModel):
    label: str
    score: float


class AdminQuizPerformancePoint(BaseModel):
    label: str
    attempts: int
    average_score: float


class AdminRiskPoint(BaseModel):
    label: str
    count: int


class AdminAnalyticsResponse(BaseModel):
    summary: AdminMetricSummary
    incident_trends: list[AdminIncidentTrendPoint]
    threat_categories: list[AdminCategoryPoint]
    awareness_scores: list[AdminAwarenessPoint]
    quiz_performance: list[AdminQuizPerformancePoint]
    email_risk_levels: list[AdminRiskPoint]
    url_risk_levels: list[AdminRiskPoint]
    generated_at: datetime
