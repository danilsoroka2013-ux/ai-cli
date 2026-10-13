"""Реестр провайдеров."""
from __future__ import annotations

from .anthropic import ClaudeProvider
from .base import BaseProvider
from .g4f import G4FProvider
from .openai_compat import (
    AlibabaProvider, DeepSeekProvider, GeminiProvider, GroqProvider,
    MistralProvider, OllamaProvider, OpenAIProvider, OpenRouterProvider,
    XAIProvider,
)

PROVIDERS: dict[str, type[BaseProvider]] = {
    cls.name: cls for cls in [
        OpenRouterProvider, GroqProvider, G4FProvider, OpenAIProvider,
        GeminiProvider, AlibabaProvider, ClaudeProvider, DeepSeekProvider,
        MistralProvider, XAIProvider, OllamaProvider,
    ]
}


def get_provider(name: str, api_key: str | None) -> BaseProvider:
    if name not in PROVIDERS:
        raise ValueError(f"Неизвестный провайдер: {name}. Доступные: {', '.join(PROVIDERS)}")
    return PROVIDERS[name](api_key)
