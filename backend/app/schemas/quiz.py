"""Schemas for database-backed quizzes and backend-graded attempts."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.dashboard import AwarenessScoreResponse


class QuizSummaryResponse(BaseModel):
    id: int
    lesson_id: int
    title: str
    description: str
    category: str
    difficulty: str
    question_count: int
    attempt_count: int
    best_score: float | None
    last_score: float | None


class QuizListResponse(BaseModel):
    quizzes: list[QuizSummaryResponse]
    categories: list[str]
    difficulties: list[str]
    total: int


class QuizQuestionResponse(BaseModel):
    id: int
    question: str
    options: list[str]


class QuizDetailResponse(QuizSummaryResponse):
    questions: list[QuizQuestionResponse]


class QuizAttemptStartResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    title: str
    category: str
    difficulty: str
    questions: list[QuizQuestionResponse]
    started_at: datetime


class SubmittedAnswer(BaseModel):
    question_id: int = Field(gt=0)
    answer: str = Field(min_length=1, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)


class QuizSubmitRequest(BaseModel):
    answers: list[SubmittedAnswer] = Field(min_length=1, max_length=100)


class AnswerResultResponse(BaseModel):
    question_id: int
    selected_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str


class QuizResultResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    score: float
    correct_answers: int
    total_questions: int
    completed_at: datetime
    results: list[AnswerResultResponse]
    awareness_score: AwarenessScoreResponse


class QuizAttemptHistoryResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_title: str
    category: str
    difficulty: str
    score: float
    total_questions: int
    completed_at: datetime


class QuizAttemptHistoryListResponse(BaseModel):
    attempts: list[QuizAttemptHistoryResponse]
    total: int
