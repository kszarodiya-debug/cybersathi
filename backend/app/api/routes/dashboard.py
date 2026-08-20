"""Student dashboard route."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import StudentOnlyAccess
from app.db.session import get_db
from app.services.dashboard import build_student_dashboard
from app.schemas.dashboard import StudentDashboardResponse


router = APIRouter(tags=["dashboard"])


@router.get("/students/dashboard", response_model=StudentDashboardResponse)
def student_dashboard(
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
) -> StudentDashboardResponse:
    return build_student_dashboard(db, current_user)
