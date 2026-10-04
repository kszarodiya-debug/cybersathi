"""Authenticated defensive email and message analysis routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import OptionalUser, StudentOnlyAccess
from app.auth.rate_limit import analysis_rate_limit
from app.db.session import get_db
from app.schemas.analysis import MessageAnalysisRequest, MessageAnalysisResponse
from app.services.analysis import persist_message_analysis


router = APIRouter(prefix="/students/analysis", tags=["analysis"])
public_router = APIRouter(prefix="/public/analysis", tags=["public-analysis"])


@router.post(
    "/messages",
    response_model=MessageAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(analysis_rate_limit)],
)
@router.post(
    "/emails",
    response_model=MessageAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(analysis_rate_limit)],
)
def analyze_message(
    payload: MessageAnalysisRequest,
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
) -> MessageAnalysisResponse:
    return persist_message_analysis(
        db,
        user_id=current_user.id,
        content=payload.message,
        content_type=payload.content_type,
    )


@public_router.post(
    "/messages",
    response_model=MessageAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(analysis_rate_limit)],
)
def analyze_public_message(
    payload: MessageAnalysisRequest,
    current_user: OptionalUser,
    db: Session = Depends(get_db),
) -> MessageAnalysisResponse:
    """Analyze a message without login; anonymous results are not persisted."""

    user_id = current_user.id if current_user and current_user.role == "student" else None
    return persist_message_analysis(
        db,
        user_id=user_id,
        content=payload.message,
        content_type=payload.content_type,
    )
