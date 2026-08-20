"""Student dashboard response schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.schemas.auth import UserResponse


class AwarenessScoreResponse(BaseModel):
    overall_score: float
    phishing_score: float
    password_score: float
    privacy_score: float
    browsing_score: float
    mobile_score: float


class QuizScoreResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_title: str
    score: float
    total_questions: int
    completed_at: datetime


class LearningProgressResponse(BaseModel):
    completed_lessons: int
    quiz_scores: list[QuizScoreResponse]
    current_streak: int


class RecentEmailAnalysisResponse(BaseModel):
    id: int
    risk_score: float
    risk_level: str
    created_at: datetime


class RecentURLAnalysisResponse(BaseModel):
    id: int
    url: str
    risk_score: float
    risk_level: str
    created_at: datetime


class RecentQuizResponse(QuizScoreResponse):
    pass


class RecentReportResponse(BaseModel):
    id: int
    incident_type: str
    status: str
    severity: str
    created_at: datetime


class RecentActivityResponse(BaseModel):
    email_analyses: list[RecentEmailAnalysisResponse]
    url_analyses: list[RecentURLAnalysisResponse]
    quizzes: list[RecentQuizResponse]
    reports: list[RecentReportResponse]


class StudentDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: UserResponse
    awareness_score: AwarenessScoreResponse | None
    learning_progress: LearningProgressResponse
    recent_activity: RecentActivityResponse
