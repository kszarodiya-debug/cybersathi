"""Database-backed Learning Hub and user progress services."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.lesson import CybersecurityLesson
from app.models.progress import LessonProgress
from app.schemas.lesson import (
    LessonCompletionResponse,
    LessonDetailResponse,
    LessonListResponse,
    LessonSummaryResponse,
)


class LessonNotFoundError(Exception):
    """Raised when a requested lesson does not exist."""


def _summary(lesson: CybersecurityLesson, progress: LessonProgress | None) -> LessonSummaryResponse:
    return LessonSummaryResponse(
        id=lesson.id,
        title=lesson.title,
        description=lesson.description,
        category=lesson.category,
        difficulty=lesson.difficulty,
        completed=bool(progress and progress.completed),
        completed_at=progress.completed_at if progress else None,
    )


def list_lessons(db: Session, *, user_id: int, category: str | None) -> LessonListResponse:
    lesson_query = select(CybersecurityLesson).order_by(CybersecurityLesson.id)
    normalized_category = category.strip().lower() if category else None
    if normalized_category:
        lesson_query = lesson_query.where(
            func.lower(CybersecurityLesson.category) == normalized_category
        )
    lessons = db.scalars(lesson_query).all()
    lesson_ids = [lesson.id for lesson in lessons]
    progress_rows = (
        db.scalars(
            select(LessonProgress).where(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id.in_(lesson_ids),
            )
        ).all()
        if lesson_ids
        else []
    )
    progress_by_lesson = {row.lesson_id: row for row in progress_rows}
    categories = list(
        db.scalars(
            select(CybersecurityLesson.category)
            .distinct()
            .order_by(CybersecurityLesson.category)
        ).all()
    )
    summaries = [_summary(lesson, progress_by_lesson.get(lesson.id)) for lesson in lessons]
    return LessonListResponse(
        lessons=summaries,
        categories=categories,
        total=len(summaries),
        completed_count=sum(1 for item in summaries if item.completed),
    )


def get_lesson(db: Session, *, user_id: int, lesson_id: int) -> LessonDetailResponse:
    lesson = db.get(CybersecurityLesson, lesson_id)
    if lesson is None:
        raise LessonNotFoundError
    progress = db.scalar(
        select(LessonProgress).where(
            LessonProgress.user_id == user_id,
            LessonProgress.lesson_id == lesson_id,
        )
    )
    summary = _summary(lesson, progress)
    return LessonDetailResponse(
        **summary.model_dump(),
        introduction=lesson.introduction,
        learning_objectives=lesson.learning_objectives,
        explanation=lesson.explanation,
        real_world_example=lesson.real_world_example,
        safety_tips=lesson.safety_tips,
        key_takeaways=lesson.key_takeaways,
    )


def complete_lesson(db: Session, *, user_id: int, lesson_id: int) -> LessonCompletionResponse:
    if db.get(CybersecurityLesson, lesson_id) is None:
        raise LessonNotFoundError
    progress = db.scalar(
        select(LessonProgress).where(
            LessonProgress.user_id == user_id,
            LessonProgress.lesson_id == lesson_id,
        )
    )
    completed_at = datetime.now(timezone.utc)
    if progress is None:
        progress = LessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            completed=True,
            completed_at=completed_at,
        )
        db.add(progress)
    else:
        progress.completed = True
        progress.completed_at = progress.completed_at or completed_at
    db.commit()
    db.refresh(progress)
    return LessonCompletionResponse(
        lesson_id=lesson_id,
        completed=progress.completed,
        completed_at=progress.completed_at or completed_at,
    )
