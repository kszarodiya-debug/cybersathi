"""Learning Hub request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LessonSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    category: str
    difficulty: str
    completed: bool
    completed_at: datetime | None


class LessonDetailResponse(LessonSummaryResponse):
    introduction: str
    learning_objectives: list[str]
    explanation: str
    real_world_example: str
    safety_tips: list[str]
    key_takeaways: list[str]


class LessonListResponse(BaseModel):
    lessons: list[LessonSummaryResponse]
    categories: list[str]
    total: int
    completed_count: int


class LessonCompletionResponse(BaseModel):
    lesson_id: int
    completed: bool
    completed_at: datetime
