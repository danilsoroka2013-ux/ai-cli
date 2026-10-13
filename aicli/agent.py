"""Агентский цикл: LLM ↔ инструменты, с подтверждениями опасных действий."""
from __future__ import annotations

import os

from . import config, tools, ui
from .providers.base import BaseProvider

def _platform_info() -> str:
    """Описание ОС и шелла для системного промпта."""
    if os.name == "nt":
        return "Windows, шелл: cmd"
    prefix = os.environ.get("PREFIX", "")
    if "com.termux" in prefix or os.environ.get("TERMUX_VERSION"):
        return "Android (Termux), шелл: bash. Пути: /data/data/com.termux/files/home"
    return "Linux/macOS, шелл: bash"


SYSTEM_PROMPT = """Ты — AI-ассистент в консоли, работающий на устройстве пользователя ({platform}).
Текущая папка: {cwd}
У тебя есть инструменты для работы с файлами, интернетом и командами ОС — используй их для выполнения задач.
Правила:
- Перед изменением файла сначала прочитай его, если он существует.
- Команды ОС пиши под текущую платформу ({platform}).
- Отвечай по-русски, кратко и по делу.
- Делай минимальные и точные изменения, ничего лишнего.
- Если задача выполнена — кратко сообщи итог.
"""


class Context:
    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve

    def confirm(self, question: str) -> bool:
        if self.auto_approve:
            ui.info(f"Авто-подтверждение: {question}")
            return True
        return ui.confirm(question)


class Agent:
    def __init__(self, provider: BaseProvider, model: str, auto_approve: bool = False):
        self.provider = provider
        self.model = model
        self.ctx = Context(auto_approve)
        cfg = config.load()
        self.max_steps = cfg.get("max_steps", 25)
        self.messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT.format(
                cwd=os.getcwd(), platform=_platform_info())}
        ]

    def reset(self) -> None:
        self.messages = self.messages[:1]

    def run(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        for step in range(self.max_steps):
            with ui.thinking(f"[{self.provider.name}/{self.model}]"):
                try:
                    reply = self.provider.chat(self.messages, tools.TOOLS, self.model)
                except Exception as e:
                    ui.error(f"Ошибка провайдера: {e}")
                    # откат истории до последнего user-сообщения, чтобы не было висячих tool_calls
                    while self.messages and self.messages[-1]["role"] != "user":
                        self.messages.pop()
                    if self.messages:
                        self.messages.pop()
                    return ""

            if not reply.tool_calls:
                self.messages.append({"role": "assistant", "content": reply.text})
                if reply.text:
                    ui.assistant_text(reply.text)
                return reply.text

            self.messages.append({
                "role": "assistant",
                "content": reply.text or None,
                "tool_calls": [{"id": tc.id, "name": tc.name, "args": tc.args} for tc in reply.tool_calls],
            })
            if reply.text:
                ui.assistant_text(reply.text)

            for tc in reply.tool_calls:
                ui.tool_call(tc.name, tc.args)
                ok, result = tools.execute(tc.name, tc.args, ctx=self.ctx)
                ui.tool_result(tc.name, result, ok)
                self.messages.append({
                    "role": "tool", "tool_call_id": tc.id, "name": tc.name,
                    "content": result[:12000],
                })

        ui.warn(f"Достигнут лимит шагов ({self.max_steps}). Остановлено.")
        return ""
