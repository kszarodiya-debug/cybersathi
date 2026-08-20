"""Administrator-only management and analytics endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.auth.dependencies import AdminAccess
from app.db.session import get_db
from app.schemas.admin import (
    AdminAnalyticsResponse,
    AdminLessonSummary,
    AdminQuizSummary,
    AdminUserResponse,
    AdminUserUpdateRequest,
)
from app.services.admin import UserManagementError, build_analytics, list_lessons, list_quizzes, list_users, update_user


router = APIRouter(tags=["admin"])


@router.get("/admin/analytics", response_model=AdminAnalyticsResponse)
def admin_analytics(current_user: AdminAccess, db: Session = Depends(get_db)) -> AdminAnalyticsResponse:
    del current_user
    return build_analytics(db)


@router.get("/admin/users", response_model=list[AdminUserResponse])
def admin_users(current_user: AdminAccess, db: Session = Depends(get_db)) -> list[AdminUserResponse]:
    del current_user
    return list_users(db)


@router.patch("/admin/users/{user_id}", response_model=AdminUserResponse)
def admin_update_user(
    user_id: Annotated[int, Path(gt=0)],
    payload: AdminUserUpdateRequest,
    current_user: AdminAccess,
    db: Session = Depends(get_db),
) -> AdminUserResponse:
    try:
        updated = update_user(
            db,
            actor_user_id=current_user.id,
            user_id=user_id,
            payload=payload,
        )
    except UserManagementError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return updated


@router.get("/admin/lessons", response_model=list[AdminLessonSummary])
def admin_lessons(current_user: AdminAccess, db: Session = Depends(get_db)) -> list[AdminLessonSummary]:
    del current_user
    return list_lessons(db)


@router.get("/admin/quizzes", response_model=list[AdminQuizSummary])
def admin_quizzes(current_user: AdminAccess, db: Session = Depends(get_db)) -> list[AdminQuizSummary]:
    del current_user
    return list_quizzes(db)
