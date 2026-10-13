"""G4F (бесплатные провайдеры, без ключа). Tool-calling через текстовый JSON-протокол."""
from __future__ import annotations

import json
import re
import uuid

from .base import BaseProvider, Reply, ToolCall

_TOOL_PROTOCOL = """
Ты можешь вызывать инструменты. Чтобы вызвать инструмент, ответь ТОЛЬКО одним блоком:
```tool
{"name": "<имя_инструмента>", "args": {<аргументы>}}
```
После этого ты получишь результат и сможешь продолжить. Доступные инструменты:
{tools}
""".strip()


class G4FProvider(BaseProvider):
    name = "g4f"
    env_key = ""
    needs_key = False
    default_model = "default"

    def __init__(self, api_key: str | None = None):
        import os
        # цепочку g4f-провайдеров можно переопределить: G4F_PROVIDER="LLM7,Cloudflare,GLM"
        self.provider_names = [n.strip() for n in
                               os.environ.get("G4F_PROVIDER", "LLM7,Cloudflare,GLM").split(",")
                               if n.strip()]

    @staticmethod
    def _sanitize(messages: list[dict]) -> list[dict]:
        """G4F не знает роль tool и поле tool_calls — переводим в обычный текст."""
        out = []
        for m in messages:
            role = m["role"]
            if role == "tool":
                out.append({"role": "user",
                            "content": f"[Результат инструмента {m.get('name', '')}]:\n{m.get('content', '')}"})
            elif role == "assistant" and m.get("tool_calls"):
                lines = [f"```tool\n{{\"name\": \"{tc['name']}\", \"args\": {json.dumps(tc['args'], ensure_ascii=False)}}}\n```"
                         for tc in m["tool_calls"]]
                out.append({"role": "assistant", "content": (m.get("content") or "") + "\n" + "\n".join(lines)})
            else:
                out.append({"role": role, "content": m.get("content") or ""})
        return out

    def _inject_protocol(self, messages: list[dict], tools: list[dict]) -> list[dict]:
        out = self._sanitize(messages)
        if not tools:
            return out
        tool_desc = "\n".join(
            f"- {t['function']['name']}: {t['function'].get('description', '')} "
            f"args={json.dumps(t['function'].get('parameters', {}).get('properties', {}), ensure_ascii=False)}"
            for t in tools
        )
        proto = _TOOL_PROTOCOL.replace("{tools}", tool_desc)
        if out and out[0]["role"] == "system":
            out[0]["content"] = (out[0].get("content") or "") + "\n\n" + proto
        else:
            out.insert(0, {"role": "system", "content": proto})
        return out

    @staticmethod
    def _parse_tool(text: str) -> ToolCall | None:
        m = re.search(r"```tool\s*\n(.*?)\n?```", text, re.DOTALL)
        if not m:
            return None
        try:
            data = json.loads(m.group(1))
            return ToolCall(id="g4f-" + uuid.uuid4().hex[:8],
                            name=data["name"], args=data.get("args", {}))
        except (json.JSONDecodeError, KeyError):
            return None

    def _make_client(self):
        import importlib
        import g4f.Provider
        from g4f.client import Client

        classes = []
        for n in self.provider_names:
            cls = None
            try:
                # после импорта подмодуля g4f.Provider.<name> атрибут пакета
                # становится модулем, поэтому класс достаём изнутри модуля
                mod = importlib.import_module(f"g4f.Provider.{n}")
                cls = getattr(mod, n, None)
            except ImportError:
                pass
            if cls is None:
                cls = getattr(g4f.Provider, n, None)
            if isinstance(cls, type):
                classes.append(cls)
        if not classes:
            return Client()
        if len(classes) == 1:
            return Client(provider=classes[0])
        from g4f.Provider import RetryProvider
        return Client(provider=RetryProvider(classes, shuffle=False))

    def chat(self, messages: list[dict], tools: list[dict], model: str) -> Reply:
        client = self._make_client()
        msgs = self._inject_protocol(messages, tools)
        # "default" — не передаём model, чтобы каждый g4f-провайдер брал свою модель
        kwargs = dict(messages=msgs)
        if model and model != "default":
            kwargs["model"] = model
        resp = client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content or ""

        tc = self._parse_tool(text)
        if tc:
            return Reply(text="", tool_calls=[tc])
        return Reply(text=text)
