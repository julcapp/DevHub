import json
import sys
from pathlib import Path

from app.workspace import apply_workspace_settings


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
CONFIG_FILE = BASE_DIR / "config" / "settings.json"
LOG_DIR = BASE_DIR / "logs"


DEFAULT_SETTINGS = {
    "workspace_root": "",
    "workspace_paths": [],
    "default_branch": "main",
    "allowed_branches": ["main", "master"],
    "exclude_folders": [
        "Archive",
        "Temp",
        "*_OLD",
        "*_BACKUP",
        "*_ARCHIVE",
        ".archive",
        "backup",
        "old",
    ],
    "skip_non_default_branch": True,
    "auto_fetch": True,
    "auto_pull": True,
    "auto_push": True,
    "create_log": True,
    "theme": "dark",
    "github_user": "julcapp",
}


def load_settings() -> dict:
    settings = dict(DEFAULT_SETTINGS)

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            loaded = json.load(file)
            settings.update(loaded)

    return apply_workspace_settings(settings, BASE_DIR)


def save_settings(settings: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, ensure_ascii=False, indent=2)


def ensure_log_dir() -> None:
    LOG_DIR.mkdir(exist_ok=True)
