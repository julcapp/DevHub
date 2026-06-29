import json
import sys
from pathlib import Path


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
CONFIG_FILE = BASE_DIR / "config" / "settings.json"
LOG_DIR = BASE_DIR / "logs"


def load_settings() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Не найден файл настроек: {CONFIG_FILE}")

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def ensure_log_dir() -> None:
    LOG_DIR.mkdir(exist_ok=True)