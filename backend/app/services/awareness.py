"""Backend-owned awareness score calculation from submitted quiz attempts."""

from collections import defaultdict
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.awareness import AwarenessScore
from app.models.lesson import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.schemas.dashboard import AwarenessScoreResponse


CATEGORY_FIELDS = {
    "phishing": "phishing_score",
    "phishing-awareness": "phishing_score",
    "password-security": "password_score",
    "password": "password_score",
    "data-privacy": "privacy_score",
    "privacy": "privacy_score",
    "safe-browsing": "browsing_score",
    "browsing": "browsing_score",
    "mobile-security": "mobile_score",
    "mobile": "mobile_score",
}


def calculate_awareness_score(db: Session, *, user_id: int) -> AwarenessScoreResponse:
    """Recalculate all awareness dimensions from immutable, submitted attempts."""

    rows = db.execute(
        select(Quiz.category, QuizAttempt.score)
        .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
        .where(
            QuizAttempt.user_id == user_id,
            QuizAttempt.status == "submitted",
        )
    ).all()

    category_scores: dict[str, list[float]] = defaultdict(list)
    all_scores: list[float] = []
    for category, score in rows:
        numeric_score = float(score)
        all_scores.append(numeric_score)
        field = CATEGORY_FIELDS.get(category.lower())
        if field:
            category_scores[field].append(numeric_score)

    values = {
        "phishing_score": round(mean(category_scores["phishing_score"]), 2)
        if category_scores["phishing_score"]
        else 0.0,
        "password_score": round(mean(category_scores["password_score"]), 2)
        if category_scores["password_score"]
        else 0.0,
        "privacy_score": round(mean(category_scores["privacy_score"]), 2)
        if category_scores["privacy_score"]
        else 0.0,
        "browsing_score": round(mean(category_scores["browsing_score"]), 2)
        if category_scores["browsing_score"]
        else 0.0,
        "mobile_score": round(mean(category_scores["mobile_score"]), 2)
        if category_scores["mobile_score"]
        else 0.0,
    }
    values["score"] = round(mean(all_scores), 2) if all_scores else 0.0

    awareness = db.scalar(select(AwarenessScore).where(AwarenessScore.user_id == user_id))
    if awareness is None:
        awareness = AwarenessScore(user_id=user_id, **values)
        db.add(awareness)
    else:
        for field, value in values.items():
            setattr(awareness, field, value)
    db.flush()

    return AwarenessScoreResponse(
        overall_score=float(values["score"]),
        phishing_score=float(values["phishing_score"]),
        password_score=float(values["password_score"]),
        privacy_score=float(values["privacy_score"]),
        browsing_score=float(values["browsing_score"]),
        mobile_score=float(values["mobile_score"]),
    )
