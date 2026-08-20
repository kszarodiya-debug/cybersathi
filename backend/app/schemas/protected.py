"""Schemas for protected route shells."""

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class FeatureStatusResponse(BaseModel):
    feature: str
    user_id: int
    message: str


class UrlAnalysisRequest(BaseModel):
    url: AnyHttpUrl


class EmailAnalysisRequest(BaseModel):
    email_content: str = Field(min_length=1, max_length=100_000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)


class IncidentReportRequest(BaseModel):
    incident_type: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=10, max_length=20_000)
    suspicious_url: AnyHttpUrl | None = None


class QuizAttemptRequest(BaseModel):
    answers: list[str] = Field(min_length=1, max_length=100)

    model_config = ConfigDict(str_strip_whitespace=True)
