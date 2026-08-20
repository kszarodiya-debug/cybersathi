"""Student incident reporting and admin report-management routes."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import AdminAccess, StudentOnlyAccess
from app.auth.rate_limit import submission_rate_limit
from app.db.session import get_db
from app.schemas.incident import (
    IncidentAdminReportListResponse,
    IncidentAdminReportResponse,
    IncidentAdminUpdateRequest,
    IncidentCreateRequest,
    IncidentReportListResponse,
    IncidentReportResponse,
)
from app.services.incidents import (
    EmptyAdminUpdateError,
    IncidentNotFoundError,
    create_report,
    get_admin_report,
    get_student_report,
    list_admin_reports,
    list_student_reports,
    update_admin_report,
)


router = APIRouter(tags=["incidents"])


@router.get("/students/incidents", response_model=IncidentReportListResponse)
def student_incident_history(
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
) -> IncidentReportListResponse:
    return list_student_reports(db, user_id=current_user.id)


@router.post(
    "/students/incidents",
    response_model=IncidentReportResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(submission_rate_limit)],
)
def submit_student_incident(
    payload: IncidentCreateRequest,
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
) -> IncidentReportResponse:
    return create_report(db, user_id=current_user.id, payload=payload)


@router.get("/students/incidents/{report_id}", response_model=IncidentReportResponse)
def student_incident_detail(
    report_id: Annotated[int, Path(gt=0)],
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
) -> IncidentReportResponse:
    try:
        return get_student_report(db, user_id=current_user.id, report_id=report_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident report not found.") from None


@router.get("/admin/incidents", response_model=IncidentAdminReportListResponse)
def admin_incident_list(
    current_user: AdminAccess,
    db: Session = Depends(get_db),
    status_filter: Annotated[
        Literal["OPEN", "UNDER_REVIEW", "RESOLVED", "REJECTED"] | None,
        Query(alias="status"),
    ] = None,
    severity: Annotated[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] | None, Query()] = None,
    incident_type: Annotated[str | None, Query(max_length=100)] = None,
) -> IncidentAdminReportListResponse:
    del current_user
    return list_admin_reports(
        db,
        status_filter=status_filter,
        severity_filter=severity,
        incident_type=incident_type,
    )


@router.get("/admin/incidents/{report_id}", response_model=IncidentAdminReportResponse)
def admin_incident_detail(
    report_id: Annotated[int, Path(gt=0)],
    current_user: AdminAccess,
    db: Session = Depends(get_db),
) -> IncidentAdminReportResponse:
    del current_user
    try:
        return get_admin_report(db, report_id=report_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident report not found.") from None


@router.patch("/admin/incidents/{report_id}", response_model=IncidentAdminReportResponse)
def update_incident(
    report_id: Annotated[int, Path(gt=0)],
    payload: IncidentAdminUpdateRequest,
    current_user: AdminAccess,
    db: Session = Depends(get_db),
) -> IncidentAdminReportResponse:
    try:
        return update_admin_report(
            db,
            report_id=report_id,
            actor_user_id=current_user.id,
            payload=payload,
        )
    except IncidentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident report not found.") from None
    except EmptyAdminUpdateError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide a new status or severity.",
        ) from None
