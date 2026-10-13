"""Файловые инструменты: чтение, запись, правка, удаление, переименование и т.д."""
from __future__ import annotations

import glob as globmod
import os
import re
import shutil
from pathlib import Path

from .. import ui


def _ok(text: str) -> tuple[bool, str]:
    return True, text


def _err(text: str) -> tuple[bool, str]:
    return False, f"Ошибка: {text}"


def read_file(path: str, offset: int = 1, limit: int = 2000, **_) -> tuple[bool, str]:
    p = Path(path)
    if not p.is_file():
        return _err(f"файл не найден: {path}")
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        return _err(str(e))
    total = len(lines)
    chunk = lines[max(offset - 1, 0): offset - 1 + limit]
    numbered = "\n".join(f"{i + offset}: {l}" for i, l in enumerate(chunk))
    ui.file_content(str(p), "\n".join(chunk))
    return _ok(f"Файл {path} (всего строк: {total}, показано: {len(chunk)}):\n{numbered}")


def write_file(path: str, content: str, ctx=None, **_) -> tuple[bool, str]:
    p = Path(path)
    try:
        if p.exists():
            old = p.read_text(encoding="utf-8", errors="replace")
            ui.diff(old, content, str(p))
            if ctx and not ctx.confirm(f"Перезаписать {path}?"):
                return _err("отменено пользователем")
        else:
            ui.info(f"Создание нового файла [bold]{path}[/bold] ({len(content)} симв.)")
            if ctx and not ctx.confirm(f"Создать {path}?"):
                return _err("отменено пользователем")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return _ok(f"Файл записан: {path} ({len(content)} симв.)")
    except Exception as e:
        return _err(str(e))


def edit_file(path: str, old_string: str, new_string: str, replace_all: bool = False, ctx=None, **_) -> tuple[bool, str]:
    p = Path(path)
    if not p.is_file():
        return _err(f"файл не найден: {path}")
    try:
        text = p.read_text(encoding="utf-8")
    except Exception as e:
        return _err(str(e))
    count = text.count(old_string)
    if count == 0:
        return _err("old_string не найден в файле")
    if count > 1 and not replace_all:
        return _err(f"old_string встречается {count} раз. Уточните строку или replace_all=true")
    new_text = text.replace(old_string, new_string) if replace_all else text.replace(old_string, new_string, 1)
    ui.diff(text, new_text, str(p))
    if ctx and not ctx.confirm(f"Применить правку в {path}?"):
        return _err("отменено пользователем")
    p.write_text(new_text, encoding="utf-8")
    return _ok(f"Файл изменён: {path} (замен: {count if replace_all else 1})")


def append_file(path: str, content: str, **_) -> tuple[bool, str]:
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return _ok(f"Добавлено {len(content)} симв. в {path}")
    except Exception as e:
        return _err(str(e))


def delete_path(path: str, ctx=None, **_) -> tuple[bool, str]:
    p = Path(path)
    if not p.exists():
        return _err(f"не найдено: {path}")
    kind = "папку" if p.is_dir() else "файл"
    if ctx and not ctx.confirm(f"Удалить {kind} [bold red]{path}[/bold red]?"):
        return _err("отменено пользователем")
    try:
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return _ok(f"Удалено: {path}")
    except Exception as e:
        return _err(str(e))


def rename_file(src: str, dst: str, ctx=None, **_) -> tuple[bool, str]:
    if not Path(src).exists():
        return _err(f"не найдено: {src}")
    if ctx and not ctx.confirm(f"Переименовать {src} → {dst}?"):
        return _err("отменено пользователем")
    try:
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        os.rename(src, dst)
        return _ok(f"Переименовано: {src} → {dst}")
    except Exception as e:
        return _err(str(e))


def move_file(src: str, dst: str, ctx=None, **_) -> tuple[bool, str]:
    if not Path(src).exists():
        return _err(f"не найдено: {src}")
    if ctx and not ctx.confirm(f"Переместить {src} → {dst}?"):
        return _err("отменено пользователем")
    try:
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)
        return _ok(f"Перемещено: {src} → {dst}")
    except Exception as e:
        return _err(str(e))


def copy_file(src: str, dst: str, **_) -> tuple[bool, str]:
    if not Path(src).exists():
        return _err(f"не найдено: {src}")
    try:
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        if Path(src).is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return _ok(f"Скопировано: {src} → {dst}")
    except Exception as e:
        return _err(str(e))


def create_directory(path: str, **_) -> tuple[bool, str]:
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return _ok(f"Папка создана: {path}")
    except Exception as e:
        return _err(str(e))


def list_directory(path: str = ".", **_) -> tuple[bool, str]:
    p = Path(path)
    if not p.is_dir():
        return _err(f"папка не найдена: {path}")
    entries = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    lines = []
    for e in entries[:500]:
        if e.is_dir():
            lines.append(f"[dir]  {e.name}/")
        else:
            lines.append(f"[file] {e.name} ({e.stat().st_size} б)")
    return _ok(f"Содержимое {p.resolve()} ({len(entries)}):\n" + "\n".join(lines))


def glob_files(pattern: str, path: str = ".", **_) -> tuple[bool, str]:
    matches = globmod.glob(str(Path(path) / pattern), recursive=True)
    matches = matches[:300]
    return _ok(f"Найдено {len(matches)} по '{pattern}':\n" + "\n".join(matches))


def grep_files(pattern: str, path: str = ".", include: str = "*", **_) -> tuple[bool, str]:
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return _err(f"неверный regex: {e}")
    hits = []
    for fp in globmod.glob(str(Path(path) / "**" / include), recursive=True):
        if not Path(fp).is_file():
            continue
        try:
            for i, line in enumerate(Path(fp).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{fp}:{i}: {line.strip()[:150]}")
                    if len(hits) >= 200:
                        break
        except Exception:
            continue
        if len(hits) >= 200:
            break
    if not hits:
        return _ok(f"Совпадений '{pattern}' не найдено")
    return _ok(f"Найдено {len(hits)} совпадений:\n" + "\n".join(hits))


def file_info(path: str, **_) -> tuple[bool, str]:
    p = Path(path)
    if not p.exists():
        return _err(f"не найдено: {path}")
    st = p.stat()
    import datetime
    return _ok(
        f"Путь: {p.resolve()}\nТип: {'папка' if p.is_dir() else 'файл'}\n"
        f"Размер: {st.st_size} б\nИзменён: {datetime.datetime.fromtimestamp(st.st_mtime)}"
    )
