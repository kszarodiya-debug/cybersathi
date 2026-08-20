"""Authenticated, non-invasive URL security analysis routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import StudentOnlyAccess
from app.auth.rate_limit import analysis_rate_limit
from app.db.session import get_db
from app.schemas.url_analysis import URLAnalysisRequest, URLAnalysisResponse
from app.services.url_analysis import get_url_history, persist_url_analysis


router = APIRouter(prefix="/students/analysis", tags=["url-analysis"])


@router.post(
    "/urls",
    response_model=URLAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(analysis_rate_limit)],
)
def analyze_url(
    payload: URLAnalysisRequest,
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
) -> URLAnalysisResponse:
    return persist_url_analysis(db, user_id=current_user.id, url=payload.url)


@router.get("/urls/history", response_model=list[URLAnalysisResponse])
def url_history(
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[URLAnalysisResponse]:
    return get_url_history(db, user_id=current_user.id, limit=limit)
