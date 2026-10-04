"""Authenticated CyberSathi assistant routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.ai.provider import (
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderResponseError,
    AIProviderTimeoutError,
    AIProvider,
    get_ai_provider,
)
from app.auth.dependencies import OptionalUser, StudentOnlyAccess
from app.auth.rate_limit import chat_rate_limit, submission_rate_limit
from app.db.session import get_db
from app.models.chat import ChatHistory
from app.schemas.chat import ChatHistoryResponse, ChatMessageResponse, ChatRequest, ClearChatResponse
from app.services.chat import answer_message


router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/history", response_model=ChatHistoryResponse)
def chat_history(
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ChatHistoryResponse:
    rows = db.scalars(
        select(ChatHistory)
        .where(ChatHistory.user_id == current_user.id)
        .order_by(desc(ChatHistory.created_at), desc(ChatHistory.id))
        .limit(limit)
    ).all()
    return ChatHistoryResponse(messages=list(reversed(rows)))


@router.post(
    "",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(chat_rate_limit)],
)
async def send_chat_message(
    payload: ChatRequest,
    current_user: OptionalUser,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
) -> ChatMessageResponse:
    try:
        history = await answer_message(
            db,
            user_id=current_user.id if current_user and current_user.role == "student" else None,
            message=payload.message,
            provider=provider,
        )
    except AIProviderConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The CyberSathi assistant is not configured yet.",
        ) from None
    except AIProviderTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The assistant took too long to respond. Please try again.",
        ) from None
    except (AIProviderResponseError, AIProviderError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The assistant is temporarily unavailable. Please try again.",
        ) from None
    return history


@router.delete(
    "/history",
    response_model=ClearChatResponse,
    dependencies=[Depends(submission_rate_limit)],
)
def clear_chat_history(
    current_user: StudentOnlyAccess,
    db: Session = Depends(get_db),
) -> ClearChatResponse:
    result = db.execute(delete(ChatHistory).where(ChatHistory.user_id == current_user.id))
    db.commit()
    return ClearChatResponse(deleted_count=result.rowcount or 0)
