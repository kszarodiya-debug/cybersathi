"""Administrator-only management and analytics endpoints."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import AdminAccess
from app.db.session import get_db
from app.schemas.admin import (
    AdminAnalyticsResponse,
    AdminActivityResponse,
    AdminLessonSummary,
    AdminQuizSummary,
    AdminStatsResponse,
    AdminUserDetailResponse,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdateRequest,
)
from app.services.admin import (
    UserManagementError,
    build_activity,
    build_analytics,
    get_admin_stats,
    get_user_detail,
    list_lessons,
    list_quizzes,
    list_users,
    update_user,
)


router = APIRouter(tags=["admin"])


@router.get("/admin/analytics", response_model=AdminAnalyticsResponse)
def admin_analytics(current_user: AdminAccess, db: Session = Depends(get_db)) -> AdminAnalyticsResponse:
    del current_user
    return build_analytics(db)


@router.get("/admin/stats", response_model=AdminStatsResponse)
def admin_stats(current_user: AdminAccess, db: Session = Depends(get_db)) -> AdminStatsResponse:
    del current_user
    return get_admin_stats(db)


@router.get("/admin/activity", response_model=AdminActivityResponse)
def admin_activity(current_user: AdminAccess, db: Session = Depends(get_db)) -> AdminActivityResponse:
    del current_user
    return build_activity(db)


@router.get("/admin/users", response_model=AdminUserListResponse)
def admin_users(
    current_user: AdminAccess,
    db: Session = Depends(get_db),
    page: Annotated[int, Query(ge=1, le=10000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(max_length=100)] = None,
    role: Annotated[Literal["student", "faculty", "admin"] | None, Query()] = None,
    department: Annotated[str | None, Query(max_length=120)] = None,
    sort: Annotated[Literal["created_at_asc", "created_at_desc"], Query()] = "created_at_desc",
) -> AdminUserListResponse:
    del current_user
    return list_users(db, page=page, page_size=page_size, search=search, role=role, department=department, sort=sort)


@router.get("/admin/users/{user_id}", response_model=AdminUserDetailResponse)
def admin_user_detail(
    user_id: Annotated[int, Path(gt=0)],
    current_user: AdminAccess,
    db: Session = Depends(get_db),
) -> AdminUserDetailResponse:
    del current_user
    user = get_user_detail(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


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
