"""Application service for safe, user-scoped CyberSathi conversations."""

from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.ai.provider import AIProvider, ProviderMessage
from app.ai.safety import CYBERSATHI_SYSTEM_PROMPT, enforce_safe_output, safety_response_for
from app.core.config import settings
from app.models.chat import ChatHistory
from app.schemas.chat import ChatMessageResponse


def _recent_history(db: Session | None, user_id: int | None) -> list[ChatHistory]:
    if user_id is None or db is None:
        return []
    rows = db.scalars(
        select(ChatHistory)
        .where(ChatHistory.user_id == user_id)
        .order_by(desc(ChatHistory.created_at), desc(ChatHistory.id))
        .limit(settings.ai_max_history_messages)
    ).all()
    return list(reversed(rows))


def _provider_messages(history: Sequence[ChatHistory], message: str) -> list[ProviderMessage]:
    messages = [ProviderMessage(role="system", content=CYBERSATHI_SYSTEM_PROMPT)]
    for turn in history:
        messages.extend(
            (
                ProviderMessage(role="user", content=turn.message),
                ProviderMessage(role="assistant", content=turn.response),
            )
        )
    messages.append(ProviderMessage(role="user", content=message))
    return messages


async def answer_message(
    db: Session | None,
    *,
    user_id: int | None,
    message: str,
    provider: AIProvider,
) -> ChatMessageResponse:
    """Generate a response and persist it only for an authenticated student."""

    response = safety_response_for(message)
    if response is None:
        response = await provider.generate(_provider_messages(_recent_history(db, user_id), message))
        response = enforce_safe_output(response)

    if user_id is None:
        return ChatMessageResponse(
            id=None,
            message=message,
            response=response,
            created_at=datetime.now(timezone.utc),
        )

    if db is None:
        raise RuntimeError("A database session is required to persist an authenticated chat message.")

    history = ChatHistory(user_id=user_id, message=message, response=response)
    db.add(history)
    db.commit()
    db.refresh(history)
    return ChatMessageResponse.model_validate(history)
