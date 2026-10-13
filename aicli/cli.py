"""CLI: chat / ask / keys / providers / models."""
from __future__ import annotations

import argparse
import sys

from rich.prompt import Prompt

from . import config, ui
from .providers import PROVIDERS, get_provider


def _make_agent(args):
    name = args.provider or config.load()["provider"]
    if name not in PROVIDERS:
        ui.error(f"Неизвестный провайдер '{name}'. Список: ai-cli providers")
        sys.exit(1)
    cls = PROVIDERS[name]
    key = config.get_key(name, cls.env_key)
    if cls.needs_key and not key:
        ui.error(f"Нет API-ключа для '{name}'.")
        ui.info(f"Задайте: ai-cli keys set {name} <ключ>   или переменная окружения {cls.env_key}")
        sys.exit(1)
    try:
        provider = get_provider(name, key)
    except Exception as e:
        ui.error(str(e))
        sys.exit(1)
    model = args.model or config.get_model(name, cls.default_model)
    from .agent import Agent
    return Agent(provider, model, auto_approve=args.yes or config.load().get("auto_approve", False))


def cmd_chat(args) -> None:
    agent = _make_agent(args)
    ui.banner()
    ui.info(f"Провайдер: [bold]{agent.provider.name}[/bold] · Модель: [bold]{agent.model}[/bold] · "
            f"Авто-подтверждение: {'вкл' if agent.ctx.auto_approve else 'выкл'}")
    while True:
        try:
            text = Prompt.ask("\n[bold green]Вы[/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            console_newline()
            break
        if not text:
            continue
        low = text.lower()
        if low in ("exit", "quit", "выход", "/exit"):
            break
        if low in ("help", "/help", "?"):
            ui.info("Команды: exit — выход · clear — очистить историю · model <имя> — сменить модель")
            continue
        if low in ("clear", "/clear"):
            agent.reset()
            ui.success("История очищена")
            continue
        if low.startswith(("model ", "/model ")):
            agent.model = text.split(maxsplit=1)[1]
            config.set_model(agent.provider.name, agent.model)
            ui.success(f"Модель: {agent.model}")
            continue
        try:
            agent.run(text)
        except KeyboardInterrupt:
            ui.warn("Прервано пользователем")


def console_newline():
    ui.console.print()


def cmd_ask(args) -> None:
    agent = _make_agent(args)
    agent.run(" ".join(args.prompt))


def cmd_providers(_args) -> None:
    cfg = config.load()
    rows = []
    for name, cls in PROVIDERS.items():
        has_key = bool(config.get_key(name, cls.env_key))
        key_status = "[green]✔[/green]" if has_key else ("[dim]не нужен[/dim]" if not cls.needs_key else "[red]✖[/red]")
        model = cfg["models"].get(name, cls.default_model)
        mark = " [bold cyan](текущий)[/bold cyan]" if name == cfg["provider"] else ""
        table_name = name + mark
        rows.append((table_name, model, key_status, "да" if cls.needs_key else "нет"))
    ui.providers_table(rows)


def cmd_keys(args) -> None:
    if args.keys_cmd == "set":
        if args.provider not in PROVIDERS:
            ui.error(f"Неизвестный провайдер: {args.provider}")
            return
        config.set_key(args.provider, args.key)
        ui.success(f"Ключ для '{args.provider}' сохранён в {config.CONFIG_FILE}")
    elif args.keys_cmd == "remove":
        if config.remove_key(args.provider):
            ui.success(f"Ключ для '{args.provider}' удалён")
        else:
            ui.warn(f"Ключа для '{args.provider}' не было")
    else:  # list
        cfg = config.load()
        for name, cls in PROVIDERS.items():
            key = cfg["keys"].get(name)
            masked = key[:6] + "..." + key[-4:] if key and len(key) > 12 else ("✔" if key else "—")
            env = f" (env: {cls.env_key})" if cls.env_key else ""
            ui.console.print(f"  [bold]{name:<12}[/bold] {masked}{env}")


def cmd_use(args) -> None:
    if args.provider not in PROVIDERS:
        ui.error(f"Неизвестный провайдер: {args.provider}")
        return
    cfg = config.load()
    cfg["provider"] = args.provider
    config.save(cfg)
    ui.success(f"Провайдер по умолчанию: {args.provider}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ai-cli", description="AI CLI с инструментами и разными провайдерами")
    sub = p.add_subparsers(dest="cmd")

    def common(sp):
        sp.add_argument("-p", "--provider", help="провайдер (openrouter, groq, g4f, openai, gemini, alibaba, claude...)")
        sp.add_argument("-m", "--model", help="модель")
        sp.add_argument("-y", "--yes", action="store_true", help="авто-подтверждение действий")

    sp = sub.add_parser("chat", help="интерактивный чат")
    common(sp)
    sp.set_defaults(func=cmd_chat)

    sp = sub.add_parser("ask", help="один запрос")
    sp.add_argument("prompt", nargs="+")
    common(sp)
    sp.set_defaults(func=cmd_ask)

    sp = sub.add_parser("providers", help="список провайдеров")
    sp.set_defaults(func=cmd_providers)

    sp = sub.add_parser("keys", help="управление API-ключами")
    ksub = sp.add_subparsers(dest="keys_cmd")
    kset = ksub.add_parser("set")
    kset.add_argument("provider")
    kset.add_argument("key")
    krem = ksub.add_parser("remove")
    krem.add_argument("provider")
    ksub.add_parser("list")
    sp.set_defaults(func=cmd_keys)

    sp = sub.add_parser("use", help="провайдер по умолчанию")
    sp.add_argument("provider")
    sp.set_defaults(func=cmd_use)

    return p


def main() -> None:
    args = build_parser().parse_args()
    if not getattr(args, "func", None):
        # без аргументов — сразу в чат
        args = build_parser().parse_args(["chat"])
    args.func(args)
