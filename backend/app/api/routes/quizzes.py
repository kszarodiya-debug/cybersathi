"""Authenticated quiz catalog, attempts, grading, and history routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import StudentOnlyAccess
from app.auth.rate_limit import submission_rate_limit
from app.db.session import get_db
from app.schemas.quiz import (
    QuizAttemptHistoryListResponse,
    QuizAttemptStartResponse,
    QuizDetailResponse,
    QuizListResponse,
    QuizResultResponse,
    QuizSubmitRequest,
)
from app.services.quizzes import (
    AttemptAlreadySubmittedError,
    AttemptNotFoundError,
    InvalidQuizAnswersError,
    QuizHasNoQuestionsError,
    QuizNotFoundError,
    get_quiz,
    list_attempt_history,
    list_quizzes,
    start_attempt,
    submit_attempt,
)


router = APIRouter(prefix="/students", tags=["quizzes"])


@router.get("/quizzes", response_model=QuizListResponse)
def quizzes(
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
    category: Annotated[str | None, Query(max_length=100)] = None,
    difficulty: Annotated[str | None, Query(max_length=20)] = None,
) -> QuizListResponse:
    return list_quizzes(
        db,
        user_id=current_user.id,
        category=category,
        difficulty=difficulty,
    )


@router.get("/quizzes/{quiz_id}", response_model=QuizDetailResponse)
def quiz_detail(
    quiz_id: Annotated[int, Path(gt=0)],
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
) -> QuizDetailResponse:
    try:
        return get_quiz(db, quiz_id=quiz_id, user_id=current_user.id)
    except QuizNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.") from None


@router.post(
    "/quizzes/{quiz_id}/attempts",
    response_model=QuizAttemptStartResponse,
    status_code=201,
    dependencies=[Depends(submission_rate_limit)],
)
def begin_quiz_attempt(
    quiz_id: Annotated[int, Path(gt=0)],
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
) -> QuizAttemptStartResponse:
    try:
        return start_attempt(db, user_id=current_user.id, quiz_id=quiz_id)
    except QuizNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.") from None
    except QuizHasNoQuestionsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This quiz is not ready yet.",
        ) from None


@router.post(
    "/quizzes/{quiz_id}/attempts/{attempt_id}/submit",
    response_model=QuizResultResponse,
    dependencies=[Depends(submission_rate_limit)],
)
def submit_quiz_attempt(
    quiz_id: Annotated[int, Path(gt=0)],
    attempt_id: Annotated[int, Path(gt=0)],
    payload: QuizSubmitRequest,
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
) -> QuizResultResponse:
    try:
        return submit_attempt(
            db,
            user_id=current_user.id,
            quiz_id=quiz_id,
            attempt_id=attempt_id,
            answers=[(answer.question_id, answer.answer) for answer in payload.answers],
        )
    except AttemptNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found.") from None
    except AttemptAlreadySubmittedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This quiz attempt has already been submitted.",
        ) from None
    except InvalidQuizAnswersError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from None


@router.get("/quiz-attempts", response_model=QuizAttemptHistoryListResponse)
def quiz_attempt_history(
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> QuizAttemptHistoryListResponse:
    return list_attempt_history(db, user_id=current_user.id, limit=limit)
