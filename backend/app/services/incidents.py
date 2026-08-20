"""Incident reporting and privileged report-management services."""

from datetime import timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.audit import AuditLog
from app.models.incident import IncidentReport
from app.models.user import User
from app.schemas.incident import (
    IncidentAdminReportListResponse,
    IncidentAdminReportResponse,
    IncidentAdminUpdateRequest,
    IncidentCreateRequest,
    IncidentReportListResponse,
    IncidentReportResponse,
)


class IncidentNotFoundError(Exception):
    """Raised when a report is absent or not visible to the current user."""


class EmptyAdminUpdateError(Exception):
    """Raised when an administrator submits no changes."""


def _normalize_datetime(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _student_response(report: IncidentReport) -> IncidentReportResponse:
    return IncidentReportResponse(
        id=report.id,
        user_id=report.user_id,
        incident_type=report.incident_type,
        description=report.description,
        suspicious_url=report.suspicious_url,
        occurred_at=_normalize_datetime(report.occurred_at),
        evidence_metadata=report.evidence_metadata,
        status=report.status,
        severity=report.severity,
        created_at=_normalize_datetime(report.created_at),
        updated_at=_normalize_datetime(report.updated_at),
    )


def _admin_response(report: IncidentReport) -> IncidentAdminReportResponse:
    response = _student_response(report)
    return IncidentAdminReportResponse(
        **response.model_dump(),
        reporter_name=report.user.name,
        reporter_email=report.user.email,
        reporter_department=report.user.department,
    )


def create_report(
    db: Session,
    *,
    user_id: int,
    payload: IncidentCreateRequest,
) -> IncidentReportResponse:
    report = IncidentReport(
        user_id=user_id,
        incident_type=payload.incident_type,
        description=payload.description,
        suspicious_url=str(payload.suspicious_url) if payload.suspicious_url else None,
        occurred_at=payload.occurred_at,
        evidence_metadata=payload.evidence_metadata,
        status="OPEN",
        severity="MEDIUM",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return _student_response(report)


def list_student_reports(
    db: Session,
    *,
    user_id: int,
) -> IncidentReportListResponse:
    reports = db.scalars(
        select(IncidentReport)
        .where(IncidentReport.user_id == user_id)
        .order_by(desc(IncidentReport.created_at))
    ).all()
    return IncidentReportListResponse(
        reports=[_student_response(report) for report in reports],
        total=len(reports),
    )


def get_student_report(
    db: Session,
    *,
    user_id: int,
    report_id: int,
) -> IncidentReportResponse:
    report = db.scalar(
        select(IncidentReport).where(
            IncidentReport.id == report_id,
            IncidentReport.user_id == user_id,
        )
    )
    if report is None:
        raise IncidentNotFoundError
    return _student_response(report)


def list_admin_reports(
    db: Session,
    *,
    status_filter: str | None = None,
    severity_filter: str | None = None,
    incident_type: str | None = None,
) -> IncidentAdminReportListResponse:
    statement = (
        select(IncidentReport)
        .options(selectinload(IncidentReport.user))
        .order_by(desc(IncidentReport.created_at))
    )
    if status_filter:
        statement = statement.where(IncidentReport.status == status_filter)
    if severity_filter:
        statement = statement.where(IncidentReport.severity == severity_filter)
    if incident_type:
        statement = statement.where(IncidentReport.incident_type == incident_type)
    reports = db.scalars(statement).all()
    return IncidentAdminReportListResponse(
        reports=[_admin_response(report) for report in reports],
        total=len(reports),
    )


def get_admin_report(db: Session, *, report_id: int) -> IncidentAdminReportResponse:
    report = db.scalar(
        select(IncidentReport)
        .options(selectinload(IncidentReport.user))
        .where(IncidentReport.id == report_id)
    )
    if report is None:
        raise IncidentNotFoundError
    return _admin_response(report)


def update_admin_report(
    db: Session,
    *,
    report_id: int,
    actor_user_id: int,
    payload: IncidentAdminUpdateRequest,
) -> IncidentAdminReportResponse:
    report = db.scalar(
        select(IncidentReport)
        .options(selectinload(IncidentReport.user))
        .where(IncidentReport.id == report_id)
        .with_for_update()
    )
    if report is None:
        raise IncidentNotFoundError
    changes: dict[str, str] = {}
    if payload.status is not None and payload.status != report.status:
        changes["status_from"] = report.status
        changes["status_to"] = payload.status
        report.status = payload.status
    if payload.severity is not None and payload.severity != report.severity:
        changes["severity_from"] = report.severity
        changes["severity_to"] = payload.severity
        report.severity = payload.severity
    if not changes:
        raise EmptyAdminUpdateError

    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action="INCIDENT_REPORT_UPDATED",
            entity_type="incident_report",
            entity_id=report.id,
            details=changes,
        )
    )
    db.commit()
    db.refresh(report)
    return _admin_response(report)
