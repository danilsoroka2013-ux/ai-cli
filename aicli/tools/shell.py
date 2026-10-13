"""Запуск консольных команд."""
from __future__ import annotations

import subprocess


def run_command(command: str, cwd: str = ".", timeout: int = 120, ctx=None, **_) -> tuple[bool, str]:
    if ctx and not ctx.confirm(f"Выполнить команду [bold red]{command}[/bold red]?"):
        return False, "Ошибка: отменено пользователем"
    try:
        proc = subprocess.run(command, shell=True, cwd=cwd, capture_output=True,
                              text=True, timeout=timeout, encoding="utf-8", errors="replace")
        out = (proc.stdout or "")[-6000:]
        err = (proc.stderr or "")[-3000:]
        text = f"exit code: {proc.returncode}\n"
        if out:
            text += f"stdout:\n{out}\n"
        if err:
            text += f"stderr:\n{err}"
        return proc.returncode == 0, text
    except subprocess.TimeoutExpired:
        return False, f"Ошибка: команда превысила таймаут {timeout}с"
    except Exception as e:
        return False, f"Ошибка: {e}"
