"""Application service for safe, user-scoped CyberSathi conversations."""

from collections.abc import Sequence

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.ai.provider import AIProvider, ProviderMessage
from app.ai.safety import CYBERSATHI_SYSTEM_PROMPT, enforce_safe_output, safety_response_for
from app.core.config import settings
from app.models.chat import ChatHistory


def _recent_history(db: Session, user_id: int) -> list[ChatHistory]:
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
    db: Session,
    *,
    user_id: int,
    message: str,
    provider: AIProvider,
) -> ChatHistory:
    """Generate, safety-filter, and persist one user-scoped conversation turn."""

    response = safety_response_for(message)
    if response is None:
        response = await provider.generate(_provider_messages(_recent_history(db, user_id), message))
        response = enforce_safe_output(response)

    history = ChatHistory(user_id=user_id, message=message, response=response)
    db.add(history)
    db.commit()
    db.refresh(history)
    return history
