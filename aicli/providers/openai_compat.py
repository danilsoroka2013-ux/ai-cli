"""OpenAI-совместимые провайдеры (tool-calling нативно)."""
from __future__ import annotations

import json

from .base import BaseProvider, Reply, ToolCall


class OpenAICompat(BaseProvider):
    base_url = ""
    default_headers: dict = {}

    def __init__(self, api_key: str | None):
        self.api_key = api_key or "not-needed"

    def chat(self, messages: list[dict], tools: list[dict], model: str) -> Reply:
        from openai import OpenAI  # ленивый импорт

        client = OpenAI(base_url=self.base_url, api_key=self.api_key,
                        default_headers=self.default_headers or None)
        kwargs = dict(model=model, messages=messages)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        resp = client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message

        reply = Reply(text=msg.content or "")
        for tc in msg.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {"_raw": tc.function.arguments}
            reply.tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, args=args))
        return reply


class OpenAIProvider(OpenAICompat):
    name = "openai"
    base_url = "https://api.openai.com/v1"
    env_key = "OPENAI_API_KEY"
    default_model = "gpt-4o-mini"


class OpenRouterProvider(OpenAICompat):
    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1"
    env_key = "OPENROUTER_API_KEY"
    default_model = "openai/gpt-4o-mini"
    default_headers = {"HTTP-Referer": "https://ai-cli.local", "X-Title": "ai-cli"}


class GroqProvider(OpenAICompat):
    name = "groq"
    base_url = "https://api.groq.com/openai/v1"
    env_key = "GROQ_API_KEY"
    default_model = "llama-3.3-70b-versatile"


class AlibabaProvider(OpenAICompat):
    name = "alibaba"
    base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    env_key = "DASHSCOPE_API_KEY"
    default_model = "qwen-plus"


class GeminiProvider(OpenAICompat):
    name = "gemini"
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    env_key = "GEMINI_API_KEY"
    default_model = "gemini-2.0-flash"


class DeepSeekProvider(OpenAICompat):
    name = "deepseek"
    base_url = "https://api.deepseek.com/v1"
    env_key = "DEEPSEEK_API_KEY"
    default_model = "deepseek-chat"


class MistralProvider(OpenAICompat):
    name = "mistral"
    base_url = "https://api.mistral.ai/v1"
    env_key = "MISTRAL_API_KEY"
    default_model = "mistral-small-latest"


class XAIProvider(OpenAICompat):
    name = "xai"
    base_url = "https://api.x.ai/v1"
    env_key = "XAI_API_KEY"
    default_model = "grok-3-mini"


class OllamaProvider(OpenAICompat):
    name = "ollama"
    base_url = "http://localhost:11434/v1"
    env_key = ""
    needs_key = False
    default_model = "llama3.1"
