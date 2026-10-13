"""Красивое консольное оформление на базе Rich."""
from __future__ import annotations

import sys

# Windows: принудительно UTF-8, чтобы работали юникод-символы
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console()

BANNER = r"""
   [bold cyan]_  ____  [/]      [bold magenta]____ _     ___ [/]
  [bold cyan]/ \(_  _) [/]     [bold magenta]/ ___) |   |_ _|[/]
 [bold cyan]/ _ \ )(   [/]_____[bold magenta]( (__| |__  | | [/]
 [bold cyan]\_/\_/(__) [/]     [bold magenta]\___)_____|___|[/]
"""

_ICONS = {
    "read_file": "📖", "write_file": "📝", "edit_file": "✏️ ", "append_file": "➕",
    "delete_file": "🗑️ ", "delete_path": "🗑️ ", "rename_file": "🔀", "move_file": "🚚",
    "copy_file": "📄", "create_directory": "📁", "list_directory": "📂",
    "glob_files": "🔍", "grep_files": "🔎", "file_info": "ℹ️ ",
    "fetch_url": "🌐", "download_file": "⬇️ ", "run_command": "💻",
}


def banner() -> None:
    console.print(BANNER)
    console.print("[dim]AI-ассистент с инструментами · help — справка · exit — выход[/dim]\n")


def info(msg: str) -> None:
    console.print(f"[cyan]ℹ[/cyan] {msg}")


def success(msg: str) -> None:
    console.print(f"[green]✔[/green] {msg}")


def error(msg: str) -> None:
    console.print(f"[red]✖[/red] {msg}")


def warn(msg: str) -> None:
    console.print(f"[yellow]![/yellow] {msg}")


def thinking(text: str = "Думаю..."):
    return console.status(f"[bold cyan]{text}[/bold cyan]", spinner="dots")


def assistant_text(md: str) -> None:
    console.print(Panel(Markdown(md), border_style="cyan", title="[bold cyan]AI[/bold cyan]", padding=(0, 1)))


def _lang_for(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return {
        "py": "python", "js": "javascript", "ts": "typescript", "json": "json",
        "html": "html", "css": "css", "md": "markdown", "sh": "bash", "bat": "batch",
        "java": "java", "cpp": "cpp", "c": "c", "rs": "rust", "go": "go",
        "yml": "yaml", "yaml": "yaml", "toml": "toml", "xml": "xml", "sql": "sql",
    }.get(ext, "text")


def _preview(value: str, limit: int = 600) -> str:
    value = str(value)
    if len(value) > limit:
        return value[:limit] + f"\n... [dim](ещё {len(value) - limit} симв.)[/dim]"
    return value


def tool_call(name: str, args: dict) -> None:
    icon = _ICONS.get(name, "🔧")
    lines = Text()
    for k, v in args.items():
        sval = str(v)
        if len(sval) > 120:
            sval = sval[:120] + "…"
        lines.append(f"  {k}: ", style="bold yellow")
        lines.append(sval + "\n", style="white")
    console.print(Panel(lines or Text("  (без аргументов)", style="dim"),
                        title=f"[bold magenta]{icon} {name}[/bold magenta]",
                        border_style="magenta", padding=(0, 1)))


def tool_result(name: str, result: str, ok: bool = True) -> None:
    icon = _ICONS.get(name, "🔧")
    style = "green" if ok else "red"
    console.print(Panel(_preview(result), title=f"[dim]{icon} результат[/dim]",
                        border_style=style, padding=(0, 1)))


def file_content(path: str, content: str, max_lines: int = 40) -> None:
    lines = content.splitlines()
    snippet = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        snippet += f"\n... (ещё {len(lines) - max_lines} строк)"
    console.print(Syntax(snippet, _lang_for(path), theme="monokai", line_numbers=True))


def diff(old: str, new: str, path: str) -> None:
    import difflib
    d = difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=2)
    text = Text()
    count = 0
    for line in d:
        count += 1
        if count > 60:
            text.append("...\n", style="dim")
            break
        if line.startswith("+") and not line.startswith("+++"):
            text.append(line + "\n", style="green")
        elif line.startswith("-") and not line.startswith("---"):
            text.append(line + "\n", style="red")
        elif line.startswith("@@"):
            text.append(line + "\n", style="cyan")
        else:
            text.append(line + "\n", style="dim")
    console.print(Panel(text, title=f"[bold]diff: {path}[/bold]", border_style="yellow", padding=(0, 1)))


def confirm(question: str) -> bool:
    return Confirm.ask(f"[bold yellow]?[/bold yellow] {question}", default=False)


def providers_table(rows: list[tuple[str, str, str, str]]) -> None:
    table = Table(title="Провайдеры", border_style="cyan", header_style="bold cyan")
    table.add_column("Имя", style="bold")
    table.add_column("Модель по умолчанию")
    table.add_column("Ключ")
    table.add_column("Нужен ключ?")
    for r in rows:
        table.add_row(*r)
    console.print(table)
