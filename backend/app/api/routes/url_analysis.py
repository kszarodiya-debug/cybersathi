"""Authenticated, non-invasive URL security analysis routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import OptionalUser, StudentOnlyAccess
from app.auth.rate_limit import analysis_rate_limit
from app.db.session import get_db
from app.schemas.url_analysis import URLAnalysisRequest, URLAnalysisResponse
from app.services.url_analysis import get_url_history, persist_url_analysis


router = APIRouter(prefix="/students/analysis", tags=["url-analysis"])
public_router = APIRouter(prefix="/public/analysis", tags=["public-analysis"])


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


@public_router.post(
    "/urls",
    response_model=URLAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(analysis_rate_limit)],
)
def analyze_public_url(
    payload: URLAnalysisRequest,
    current_user: OptionalUser,
    db: Session = Depends(get_db),
) -> URLAnalysisResponse:
    """Analyze a URL without login; anonymous results are not persisted."""

    user_id = current_user.id if current_user and current_user.role == "student" else None
    return persist_url_analysis(db, user_id=user_id, url=payload.url)


@router.get("/urls/history", response_model=list[URLAnalysisResponse])
def url_history(
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[URLAnalysisResponse]:
    return get_url_history(db, user_id=current_user.id, limit=limit)
