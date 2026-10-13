"""Реестр инструментов: JSON-схемы для LLM + диспетчер выполнения."""
from __future__ import annotations

from . import filesystem as fs
from . import shell, web


def _schema(name, desc, props, required=()):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {"type": "object", "properties": props, "required": list(required)},
        },
    }


def _s(desc):
    return {"type": "string", "description": desc}


def _i(desc):
    return {"type": "integer", "description": desc}


def _b(desc):
    return {"type": "boolean", "description": desc}


TOOLS: list[dict] = [
    _schema("read_file", "Прочитать файл с номерами строк",
            {"path": _s("путь к файлу"), "offset": _i("с какой строки (1)"), "limit": _i("сколько строк")}, ["path"]),
    _schema("write_file", "Создать или перезаписать файл целиком",
            {"path": _s("путь"), "content": _s("полное содержимое файла")}, ["path", "content"]),
    _schema("edit_file", "Точечная замена текста в файле (old_string -> new_string)",
            {"path": _s("путь"), "old_string": _s("точный заменяемый фрагмент"),
             "new_string": _s("новый фрагмент"), "replace_all": _b("заменить все вхождения")},
            ["path", "old_string", "new_string"]),
    _schema("append_file", "Дописать текст в конец файла",
            {"path": _s("путь"), "content": _s("текст")}, ["path", "content"]),
    _schema("delete_path", "Удалить файл или папку (рекурсивно)", {"path": _s("путь")}, ["path"]),
    _schema("rename_file", "Переименовать файл/папку",
            {"src": _s("текущий путь"), "dst": _s("новый путь")}, ["src", "dst"]),
    _schema("move_file", "Переместить файл/папку",
            {"src": _s("откуда"), "dst": _s("куда")}, ["src", "dst"]),
    _schema("copy_file", "Скопировать файл/папку",
            {"src": _s("откуда"), "dst": _s("куда")}, ["src", "dst"]),
    _schema("create_directory", "Создать папку (включая родительские)", {"path": _s("путь")}, ["path"]),
    _schema("list_directory", "Список файлов и папок в директории",
            {"path": _s("путь, по умолчанию .")}, []),
    _schema("glob_files", "Поиск файлов по glob-паттерну (напр. **/*.py)",
            {"pattern": _s("glob-паттерн"), "path": _s("корневая папка")}, ["pattern"]),
    _schema("grep_files", "Поиск текста (regex) по файлам",
            {"pattern": _s("regex"), "path": _s("папка"), "include": _s("маска файлов, напр. *.py")}, ["pattern"]),
    _schema("file_info", "Информация о файле: размер, дата изменения", {"path": _s("путь")}, ["path"]),
    _schema("fetch_url", "Загрузить веб-страницу и получить текст/разметку",
            {"url": _s("URL"), "format": _s("text | html")}, ["url"]),
    _schema("download_file", "Скачать файл из интернета на диск",
            {"url": _s("URL файла"), "path": _s("куда сохранить")}, ["url", "path"]),
    _schema("run_command", "Выполнить консольную команду ОС",
            {"command": _s("команда"), "cwd": _s("рабочая папка"), "timeout": _i("таймаут, сек")}, ["command"]),
]

_HANDLERS = {
    "read_file": fs.read_file,
    "write_file": fs.write_file,
    "edit_file": fs.edit_file,
    "append_file": fs.append_file,
    "delete_path": fs.delete_path,
    "rename_file": fs.rename_file,
    "move_file": fs.move_file,
    "copy_file": fs.copy_file,
    "create_directory": fs.create_directory,
    "list_directory": fs.list_directory,
    "glob_files": fs.glob_files,
    "grep_files": fs.grep_files,
    "file_info": fs.file_info,
    "fetch_url": web.fetch_url,
    "download_file": web.download_file,
    "run_command": shell.run_command,
}


def execute(name: str, args: dict, ctx=None) -> tuple[bool, str]:
    handler = _HANDLERS.get(name)
    if not handler:
        return False, f"Ошибка: неизвестный инструмент '{name}'"
    try:
        return handler(ctx=ctx, **args)
    except TypeError as e:
        return False, f"Ошибка аргументов {name}: {e}"
    except Exception as e:
        return False, f"Ошибка выполнения {name}: {e}"
