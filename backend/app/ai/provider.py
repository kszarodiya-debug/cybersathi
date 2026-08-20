"""Provider abstraction for defensive CyberSathi conversations."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import settings


class AIProviderError(Exception):
    """Base error for failures in an external AI provider."""


class AIProviderConfigurationError(AIProviderError):
    """Raised when the provider is not configured safely."""


class AIProviderTimeoutError(AIProviderError):
    """Raised when a provider does not answer within the configured timeout."""


class AIProviderResponseError(AIProviderError):
    """Raised when a provider returns an unusable response."""


@dataclass(frozen=True)
class ProviderMessage:
    role: str
    content: str


class AIProvider(Protocol):
    async def generate(self, messages: Sequence[ProviderMessage]) -> str:
        """Generate one response from an ordered, already-safety-scoped prompt."""


class OpenAICompatibleProvider:
    """Call a provider exposing the OpenAI chat-completions contract."""

    def __init__(self, *, api_key: str, base_url: str, model: str, timeout: float) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    async def generate(self, messages: Sequence[ProviderMessage]) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {"role": item.role, "content": item.content} for item in messages
            ],
            "temperature": 0.2,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            raise AIProviderTimeoutError from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise AIProviderResponseError from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderResponseError from exc
        if not isinstance(content, str) or not content.strip():
            raise AIProviderResponseError
        return content.strip()


class UnconfiguredProvider:
    """Deferred configuration failure so the API can return a controlled 503."""

    async def generate(self, messages: Sequence[ProviderMessage]) -> str:
        del messages
        raise AIProviderConfigurationError


def get_ai_provider() -> AIProvider:
    """Build the configured provider without exposing credentials to callers."""

    if settings.ai_provider != "openai_compatible" or not settings.ai_api_key:
        return UnconfiguredProvider()
    return OpenAICompatibleProvider(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
        model=settings.ai_model,
        timeout=settings.ai_timeout_seconds,
    )
