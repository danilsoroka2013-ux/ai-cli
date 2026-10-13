"""Anthropic Claude (нативный tool-use)."""
from __future__ import annotations

import json

from .base import BaseProvider, Reply, ToolCall


class ClaudeProvider(BaseProvider):
    name = "claude"
    env_key = "ANTHROPIC_API_KEY"
    default_model = "claude-sonnet-4-5"

    def __init__(self, api_key: str | None):
        self.api_key = api_key

    @staticmethod
    def _convert_messages(messages: list[dict]) -> tuple[str, list[dict]]:
        """OpenAI-формат -> Anthropic-формат. Возвращает (system, messages)."""
        system = ""
        out: list[dict] = []
        for m in messages:
            role = m["role"]
            if role == "system":
                system += (m.get("content") or "") + "\n"
            elif role == "assistant":
                content: list[dict] = []
                if m.get("content"):
                    content.append({"type": "text", "text": m["content"]})
                for tc in m.get("tool_calls", []):
                    content.append({
                        "type": "tool_use", "id": tc["id"], "name": tc["name"],
                        "input": tc["args"],
                    })
                out.append({"role": "assistant", "content": content or [{"type": "text", "text": ""}]})
            elif role == "tool":
                out.append({"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": m["tool_call_id"],
                    "content": m.get("content") or "",
                }]})
            else:
                out.append({"role": "user", "content": m.get("content") or ""})
        # склеить подряд идущие user-сообщения (Anthropic требует чередования)
        merged: list[dict] = []
        for m in out:
            if merged and merged[-1]["role"] == m["role"] == "user":
                prev = merged[-1]["content"]
                cur = m["content"]
                prev_list = prev if isinstance(prev, list) else [{"type": "text", "text": prev}]
                cur_list = cur if isinstance(cur, list) else [{"type": "text", "text": cur}]
                merged[-1]["content"] = prev_list + cur_list
            else:
                merged.append(m)
        return system.strip(), merged

    @staticmethod
    def _convert_tools(tools: list[dict]) -> list[dict]:
        return [{
            "name": t["function"]["name"],
            "description": t["function"].get("description", ""),
            "input_schema": t["function"].get("parameters", {"type": "object", "properties": {}}),
        } for t in tools]

    def chat(self, messages: list[dict], tools: list[dict], model: str) -> Reply:
        import anthropic  # ленивый импорт

        client = anthropic.Anthropic(api_key=self.api_key)
        system, msgs = self._convert_messages(messages)
        kwargs = dict(model=model, max_tokens=4096, messages=msgs)
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
        resp = client.messages.create(**kwargs)

        reply = Reply()
        for block in resp.content:
            if block.type == "text":
                reply.text += block.text
            elif block.type == "tool_use":
                reply.tool_calls.append(ToolCall(id=block.id, name=block.name, args=block.input))
        return reply
