"""Хранение конфигурации и API-ключей (~/.ai-cli/config.json + переменные окружения)."""
from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".ai-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"

_DEFAULT = {
    "provider": "openrouter",
    "models": {},          # provider -> model
    "keys": {},            # provider -> api key
    "auto_approve": False,  # не спрашивать подтверждение действий
    "max_steps": 25,
}


def load() -> dict:
    cfg = dict(_DEFAULT)
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            for k, v in data.items():
                if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    cfg[k].update(v)
                else:
                    cfg[k] = v
        except Exception:
            pass
    return cfg


def save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def get_key(provider: str, env_name: str | None = None) -> str | None:
    """Ключ из конфига, затем из переменной окружения."""
    key = load()["keys"].get(provider)
    if key:
        return key
    if env_name:
        return os.environ.get(env_name)
    return None


def set_key(provider: str, key: str) -> None:
    cfg = load()
    cfg["keys"][provider] = key
    save(cfg)


def remove_key(provider: str) -> bool:
    cfg = load()
    if provider in cfg["keys"]:
        del cfg["keys"][provider]
        save(cfg)
        return True
    return False


def get_model(provider: str, default: str) -> str:
    return load()["models"].get(provider, default)


def set_model(provider: str, model: str) -> None:
    cfg = load()
    cfg["models"][provider] = model
    save(cfg)
