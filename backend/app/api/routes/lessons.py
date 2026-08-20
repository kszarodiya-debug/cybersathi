"""Authenticated Learning Hub routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import StudentOnlyAccess
from app.auth.rate_limit import submission_rate_limit
from app.db.session import get_db
from app.schemas.lesson import LessonCompletionResponse, LessonDetailResponse, LessonListResponse
from app.services.lessons import LessonNotFoundError, complete_lesson, get_lesson, list_lessons


router = APIRouter(prefix="/students/lessons", tags=["lessons"])


@router.get("", response_model=LessonListResponse)
def lessons(
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
    category: Annotated[str | None, Query(max_length=100)] = None,
) -> LessonListResponse:
    return list_lessons(db, user_id=current_user.id, category=category)


@router.get("/{lesson_id}", response_model=LessonDetailResponse)
def lesson_detail(
    lesson_id: Annotated[int, Path(gt=0)],
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
) -> LessonDetailResponse:
    try:
        return get_lesson(db, user_id=current_user.id, lesson_id=lesson_id)
    except LessonNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found.") from None


@router.post(
    "/{lesson_id}/complete",
    response_model=LessonCompletionResponse,
    dependencies=[Depends(submission_rate_limit)],
)
def mark_lesson_complete(
    lesson_id: Annotated[int, Path(gt=0)],
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
) -> LessonCompletionResponse:
    try:
        return complete_lesson(db, user_id=current_user.id, lesson_id=lesson_id)
    except LessonNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found.") from None
