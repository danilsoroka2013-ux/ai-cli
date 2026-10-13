"""Веб-инструменты: фетч страниц и скачивание файлов."""
from __future__ import annotations

import re
from pathlib import Path

import requests
from rich.progress import BarColumn, DownloadColumn, Progress, TransferSpeedColumn

from .. import ui

_HEADERS = {"User-Agent": "Mozilla/5.0 (ai-cli) Chrome/120.0"}
MAX_TEXT = 15000


def _html_to_text(html: str) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n")
    except ImportError:
        text = re.sub(r"(?s)<(script|style).*?</\1>", "", html)
        text = re.sub(r"<br\s*/?>", "\n", text)
        text = re.sub(r"</(p|div|li|h[1-6]|tr)>", "\n", text)
        text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def fetch_url(url: str, format: str = "text", **_) -> tuple[bool, str]:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        return False, f"Ошибка загрузки {url}: {e}"
    ct = r.headers.get("Content-Type", "")
    body = r.text
    if format == "text" and "html" in ct:
        body = _html_to_text(body)
    body = body[:MAX_TEXT]
    ui.info(f"GET {url} → {r.status_code}, {len(r.content)} б")
    return True, f"URL: {url}\nStatus: {r.status_code}\nContent-Type: {ct}\n\n{body}"


def download_file(url: str, path: str, ctx=None, **_) -> tuple[bool, str]:
    p = Path(path)
    if p.exists() and ctx and not ctx.confirm(f"Файл {path} существует. Перезаписать?"):
        return False, "Ошибка: отменено пользователем"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, headers=_HEADERS, timeout=60, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", 0))
            with Progress("[progress.description]{task.description}", BarColumn(),
                          DownloadColumn(), TransferSpeedColumn(), console=ui.console) as prog:
                task = prog.add_task(f"⬇ {p.name}", total=total or None)
                with open(p, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        f.write(chunk)
                        prog.update(task, advance=len(chunk))
        return True, f"Скачано: {url} → {p.resolve()} ({p.stat().st_size} б)"
    except Exception as e:
        return False, f"Ошибка скачивания {url}: {e}"
