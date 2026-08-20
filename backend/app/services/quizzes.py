"""Quiz catalog, attempt lifecycle, backend grading, and attempt history."""

from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.lesson import Quiz, QuizQuestion
from app.models.quiz_attempt import QuizAttempt
from app.schemas.quiz import (
    AnswerResultResponse,
    QuizAttemptHistoryListResponse,
    QuizAttemptHistoryResponse,
    QuizAttemptStartResponse,
    QuizDetailResponse,
    QuizListResponse,
    QuizQuestionResponse,
    QuizResultResponse,
)
from app.services.awareness import calculate_awareness_score


class QuizNotFoundError(Exception):
    """Raised when a quiz does not exist."""


class QuizHasNoQuestionsError(Exception):
    """Raised when an administrator has not populated a quiz yet."""


class AttemptNotFoundError(Exception):
    """Raised when an attempt is not owned by the authenticated user."""


class AttemptAlreadySubmittedError(Exception):
    """Raised when a client tries to submit an immutable completed attempt."""


class InvalidQuizAnswersError(Exception):
    """Raised when submitted answers do not match the quiz questions."""


def _question_response(question: QuizQuestion) -> QuizQuestionResponse:
    return QuizQuestionResponse(
        id=question.id,
        question=question.question,
        options=list(question.options),
    )


def _quiz_summary(
    quiz: Quiz,
    submitted_attempts: list[QuizAttempt],
) -> dict:
    scores = [float(attempt.score) for attempt in submitted_attempts]
    return {
        "id": quiz.id,
        "lesson_id": quiz.lesson_id,
        "title": quiz.title,
        "description": quiz.description,
        "category": quiz.category,
        "difficulty": quiz.difficulty,
        "question_count": len(quiz.questions),
        "attempt_count": len(submitted_attempts),
        "best_score": max(scores) if scores else None,
        "last_score": scores[0] if scores else None,
    }


def list_quizzes(
    db: Session,
    *,
    user_id: int,
    category: str | None = None,
    difficulty: str | None = None,
) -> QuizListResponse:
    quizzes = db.scalars(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .order_by(Quiz.category, Quiz.difficulty, Quiz.title)
    ).all()
    attempts = db.scalars(
        select(QuizAttempt)
        .where(QuizAttempt.user_id == user_id, QuizAttempt.status == "submitted")
        .order_by(desc(QuizAttempt.completed_at))
    ).all()
    by_quiz: dict[int, list[QuizAttempt]] = defaultdict(list)
    for attempt in attempts:
        by_quiz[attempt.quiz_id].append(attempt)

    normalized_category = category.strip().lower() if category else None
    normalized_difficulty = difficulty.strip().lower() if difficulty else None
    filtered = [
        quiz
        for quiz in quizzes
        if (not normalized_category or quiz.category.lower() == normalized_category)
        and (not normalized_difficulty or quiz.difficulty.lower() == normalized_difficulty)
    ]
    return QuizListResponse(
        quizzes=[_quiz_summary(quiz, by_quiz[quiz.id]) for quiz in filtered],
        categories=sorted({quiz.category for quiz in quizzes}),
        difficulties=sorted({quiz.difficulty for quiz in quizzes}),
        total=len(filtered),
    )


def get_quiz(db: Session, *, quiz_id: int, user_id: int) -> QuizDetailResponse:
    quiz = db.scalar(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id)
    )
    if quiz is None:
        raise QuizNotFoundError
    submitted_attempts = db.scalars(
        select(QuizAttempt)
        .where(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.user_id == user_id,
            QuizAttempt.status == "submitted",
        )
        .order_by(desc(QuizAttempt.completed_at))
    ).all()
    return QuizDetailResponse(
        **_quiz_summary(quiz, submitted_attempts),
        questions=[_question_response(question) for question in quiz.questions],
    )


def start_attempt(db: Session, *, user_id: int, quiz_id: int) -> QuizAttemptStartResponse:
    quiz = db.scalar(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id)
    )
    if quiz is None:
        raise QuizNotFoundError
    if not quiz.questions:
        raise QuizHasNoQuestionsError

    started_at = datetime.now(timezone.utc)
    attempt = QuizAttempt(
        user_id=user_id,
        quiz_id=quiz.id,
        score=0,
        total_questions=len(quiz.questions),
        status="in_progress",
        answers={},
        started_at=started_at,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return QuizAttemptStartResponse(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        title=quiz.title,
        category=quiz.category,
        difficulty=quiz.difficulty,
        questions=[_question_response(question) for question in quiz.questions],
        started_at=attempt.started_at,
    )


def submit_attempt(
    db: Session,
    *,
    user_id: int,
    quiz_id: int,
    attempt_id: int,
    answers: list[tuple[int, str]],
) -> QuizResultResponse:
    attempt = db.scalar(
        select(QuizAttempt)
        .options(selectinload(QuizAttempt.quiz).selectinload(Quiz.questions))
        .where(QuizAttempt.id == attempt_id, QuizAttempt.user_id == user_id)
        .with_for_update()
    )
    if attempt is None or attempt.quiz_id != quiz_id:
        raise AttemptNotFoundError
    if attempt.status != "in_progress":
        raise AttemptAlreadySubmittedError

    questions = list(attempt.quiz.questions)
    question_by_id = {question.id: question for question in questions}
    submitted_ids = [question_id for question_id, _ in answers]
    if len(submitted_ids) != len(set(submitted_ids)):
        raise InvalidQuizAnswersError("Each quiz question must be answered exactly once.")
    if set(submitted_ids) != set(question_by_id):
        raise InvalidQuizAnswersError("Submit one answer for every quiz question.")

    result_rows: list[AnswerResultResponse] = []
    correct_count = 0
    answer_map: dict[str, str] = {}
    for question_id, selected_answer in answers:
        question = question_by_id[question_id]
        if selected_answer not in question.options:
            raise InvalidQuizAnswersError("Each answer must be one of the supplied choices.")
        is_correct = selected_answer == question.correct_answer
        correct_count += int(is_correct)
        answer_map[str(question_id)] = selected_answer
        result_rows.append(
            AnswerResultResponse(
                question_id=question_id,
                selected_answer=selected_answer,
                correct_answer=question.correct_answer,
                is_correct=is_correct,
                explanation=question.explanation,
            )
        )

    completed_at = datetime.now(timezone.utc)
    score = round((correct_count / len(questions)) * 100, 2)
    attempt.status = "submitted"
    attempt.answers = answer_map
    attempt.score = score
    attempt.total_questions = len(questions)
    attempt.completed_at = completed_at
    attempt.submitted_at = completed_at
    awareness_score = calculate_awareness_score(db, user_id=user_id)
    db.commit()

    return QuizResultResponse(
        attempt_id=attempt.id,
        quiz_id=quiz_id,
        score=score,
        correct_answers=correct_count,
        total_questions=len(questions),
        completed_at=completed_at,
        results=result_rows,
        awareness_score=awareness_score,
    )


def list_attempt_history(
    db: Session,
    *,
    user_id: int,
    limit: int = 50,
) -> QuizAttemptHistoryListResponse:
    rows = db.execute(
        select(QuizAttempt, Quiz.title, Quiz.category, Quiz.difficulty)
        .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
        .where(QuizAttempt.user_id == user_id, QuizAttempt.status == "submitted")
        .order_by(desc(QuizAttempt.completed_at))
        .limit(limit)
    ).all()
    attempts = [
        QuizAttemptHistoryResponse(
            attempt_id=attempt.id,
            quiz_id=attempt.quiz_id,
            quiz_title=title,
            category=category,
            difficulty=difficulty,
            score=float(attempt.score),
            total_questions=attempt.total_questions,
            completed_at=attempt.completed_at,
        )
        for attempt, title, category, difficulty in rows
    ]
    return QuizAttemptHistoryListResponse(attempts=attempts, total=len(attempts))
