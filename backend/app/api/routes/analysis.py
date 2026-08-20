"""Authenticated defensive email and message analysis routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import StudentOnlyAccess
from app.auth.rate_limit import analysis_rate_limit
from app.db.session import get_db
from app.schemas.analysis import MessageAnalysisRequest, MessageAnalysisResponse
from app.services.analysis import persist_message_analysis


router = APIRouter(prefix="/students/analysis", tags=["analysis"])


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
