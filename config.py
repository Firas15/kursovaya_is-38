"""
config.py — Настройки приложения.

config.ini создаётся рядом с main.py (или рядом с .exe при релизе).
Содержит путь к БД и ключ шифрования.

Структура config.ini:
    [database]
    path = data/students.db         ; локальный или сетевой путь
    key  = <hex-строка>             ; ключ шифрования SQLCipher (авто)

    [app]
    configured = false              ; false = показать мастер настройки
"""

import configparser
import os
import secrets
import sys
from pathlib import Path


# ── путь к config.ini (всегда рядом с исполняемым файлом) ────────────────────

def _app_dir() -> Path:
    """
    Вернуть папку, где лежит исполняемый файл (.exe или main.py).
    Работает и в режиме скрипта, и после упаковки PyInstaller.
    """
    if getattr(sys, "frozen", False):
        # упакован PyInstaller: sys.executable = path/to/app.exe
        return Path(sys.executable).parent
    else:
        # режим разработки: main.py
        return Path(__file__).parent


CONFIG_PATH = _app_dir() / "config.ini"


# ── значения по умолчанию ─────────────────────────────────────────────────────

DEFAULTS = {
    "database": {
        "path": str(_app_dir() / "data" / "students.db"),
        "key":  "",          # будет сгенерирован при первом сохранении
    },
    "app": {
        "configured": "false",
    },
}


# ── чтение ────────────────────────────────────────────────────────────────────

def load() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    # выставить дефолты
    for section, values in DEFAULTS.items():
        cfg[section] = values
    cfg.read(str(CONFIG_PATH), encoding="utf-8")
    return cfg


def get_db_path() -> Path:
    cfg = load()
    raw = cfg.get("database", "path", fallback="").strip()
    if not raw:
        raw = DEFAULTS["database"]["path"]
    p = Path(raw)
    # если путь относительный — относительно папки приложения
    if not p.is_absolute():
        p = _app_dir() / p
    return p


def get_db_key() -> str:
    """Вернуть ключ шифрования. Если не задан — сгенерировать и сохранить."""
    cfg = load()
    key = cfg.get("database", "key", fallback="").strip()
    if not key:
        key = secrets.token_hex(32)   # 256-bit
        cfg["database"]["key"] = key
        save(cfg)
    return key


def is_configured() -> bool:
    cfg = load()
    return cfg.get("app", "configured", fallback="false").lower() == "true"


# ── запись ────────────────────────────────────────────────────────────────────

def save(cfg: configparser.ConfigParser):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(str(CONFIG_PATH), "w", encoding="utf-8") as f:
        cfg.write(f)


def save_db_path(new_path: str):
    cfg = load()
    cfg["database"]["path"] = new_path.strip()
    cfg["app"]["configured"] = "true"
    save(cfg)


def mark_configured():
    cfg = load()
    cfg["app"]["configured"] = "true"
    save(cfg)
