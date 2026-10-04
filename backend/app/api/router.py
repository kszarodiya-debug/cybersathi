"""Versioned API router."""

from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.admin import router as admin_router
from app.api.routes.chat import router as chat_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.analysis import public_router as public_analysis_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.lessons import public_router as public_lessons_router
from app.api.routes.lessons import router as lessons_router
from app.api.routes.quizzes import public_router as public_quizzes_router
from app.api.routes.quizzes import router as quizzes_router
from app.api.routes.url_analysis import public_router as public_url_analysis_router
from app.api.routes.url_analysis import router as url_analysis_router
from app.api.routes.protected import router as protected_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(analysis_router)
api_router.include_router(public_analysis_router)
api_router.include_router(url_analysis_router)
api_router.include_router(public_url_analysis_router)
api_router.include_router(lessons_router)
api_router.include_router(public_lessons_router)
api_router.include_router(quizzes_router)
api_router.include_router(public_quizzes_router)
api_router.include_router(incidents_router)
api_router.include_router(dashboard_router)
api_router.include_router(admin_router)
api_router.include_router(protected_router)
