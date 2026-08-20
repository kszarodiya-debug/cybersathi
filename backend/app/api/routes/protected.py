"""Protected route shells with role-based authorization."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.dependencies import StudentOnlyAccess, require_roles
from app.models.user import User
from app.schemas.protected import (
    ChatRequest,
    FeatureStatusResponse,
)


router = APIRouter(tags=["protected"])

StudentAccess = StudentOnlyAccess
FacultyAccess = Annotated[
    User,
    Depends(require_roles("faculty", "admin")),
]


def _feature_response(feature: str, user: User) -> FeatureStatusResponse:
    return FeatureStatusResponse(
        feature=feature,
        user_id=user.id,
        message="Protected route is available for the authenticated user.",
    )


@router.get("/lessons", response_model=FeatureStatusResponse)
def access_lessons(current_user: StudentAccess) -> FeatureStatusResponse:
    return _feature_response("lessons", current_user)


@router.post("/students/assistant/chat", response_model=FeatureStatusResponse)
def use_ai_assistant(payload: ChatRequest, current_user: StudentAccess) -> FeatureStatusResponse:
    del payload
    return _feature_response("ai-assistant", current_user)


@router.get("/faculty/awareness-statistics", response_model=FeatureStatusResponse)
def awareness_statistics(current_user: FacultyAccess) -> FeatureStatusResponse:
    return _feature_response("awareness-statistics", current_user)


@router.get("/faculty/reports", response_model=FeatureStatusResponse)
def relevant_reports(current_user: FacultyAccess) -> FeatureStatusResponse:
    return _feature_response("relevant-reports", current_user)
