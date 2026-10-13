"""Базовый интерфейс провайдера."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict


@dataclass
class Reply:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class BaseProvider:
    name = "base"
    default_model = ""
    env_key = ""            # имя переменной окружения с ключом
    needs_key = True

    def chat(self, messages: list[dict], tools: list[dict], model: str) -> Reply:
        raise NotImplementedError
