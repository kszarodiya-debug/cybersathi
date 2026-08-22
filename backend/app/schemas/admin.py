"""Schemas for administrator-only analytics and management views."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AdminUserUpdateRequest(BaseModel):
    """Fields an administrator may change without touching credentials."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

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
    last_login_at: datetime | None = None
    lessons_completed: int = 0
    quiz_attempts: int = 0
    average_quiz_score: float = 0
    awareness_score: float | None = None
    phishing_score: float | None = None
    password_score: float | None = None
    privacy_score: float | None = None
    browsing_score: float | None = None


class AdminUserListResponse(BaseModel):
    users: list[AdminUserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminActivityItem(BaseModel):
    activity_type: str
    count: int
    latest_at: datetime | None = None


class AdminUserDetailResponse(AdminUserResponse):
    recent_activity: list[AdminActivityItem]


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
    active_users: int = 0
    registered_users: int = 0
    total_quiz_attempts: int = 0
    total_incident_reports: int = 0


class AdminStatsResponse(BaseModel):
    registered_users: int
    active_users: int
    students: int
    faculty: int
    admins: int
    total_quiz_attempts: int
    total_incident_reports: int
    total_email_analyses: int
    total_url_analyses: int
    awareness_average: float
    generated_at: datetime


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


class AdminTimeSeriesPoint(BaseModel):
    label: str
    count: int


class AdminActivityResponse(BaseModel):
    registrations: list[AdminTimeSeriesPoint]
    quiz_activity: list[AdminTimeSeriesPoint]
    lesson_completions: list[AdminTimeSeriesPoint]
    email_analyses: list[AdminTimeSeriesPoint]
    url_analyses: list[AdminTimeSeriesPoint]
    incident_reports: list[AdminTimeSeriesPoint]
    generated_at: datetime


class AdminAnalyticsResponse(BaseModel):
    summary: AdminMetricSummary
    incident_trends: list[AdminIncidentTrendPoint]
    threat_categories: list[AdminCategoryPoint]
    awareness_scores: list[AdminAwarenessPoint]
    quiz_performance: list[AdminQuizPerformancePoint]
    email_risk_levels: list[AdminRiskPoint]
    url_risk_levels: list[AdminRiskPoint]
    generated_at: datetime
    awareness_distribution: list[AdminCategoryPoint] = Field(default_factory=list)
    phishing_reports: int = 0
    suspicious_url_analyses: int = 0
    high_risk_url_analyses: int = 0
    high_risk_email_analyses: int = 0
    cyber_incidents: int = 0
