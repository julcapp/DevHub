from __future__ import annotations

from pathlib import Path

from app.config import load_settings
from app.git_manager import (
    detect_sync_state,
    find_repositories,
    get_branch,
    get_local_last_commit_date,
    get_remote_last_commit_date,
)
from app.project_metadata import load_project_metadata


SYNC_STATE_RU = {
    "SYNCED": "Синхронизировано",
    "PULL_REQUIRED": "Есть изменения на GitHub",
    "PUSH_REQUIRED": "Нужно отправить изменения",
    "COMMIT_REQUIRED": "Требуется Commit",
    "DIVERGED": "Есть расхождения",
    "UNKNOWN": "Неизвестно",
    "ERROR": "Ошибка",
}


class GitWorkspaceController:
    """Подготавливает данные и команды Git Workspace без зависимости от UI."""

    def __init__(self) -> None:
        self.settings = load_settings()
        self.repositories: list[Path] = []

    def scan(self) -> list[dict[str, str]]:
        self.repositories = find_repositories(
            workspace_paths=self.settings["workspace_paths"],
            exclude_folders=self.settings.get("exclude_folders", []),
        )
        rows: list[dict[str, str]] = []
        for repository in self.repositories:
            metadata = load_project_metadata(repository)
            branch = get_branch(repository)
            state = detect_sync_state(repository, branch)
            rows.append(
                {
                    "name": metadata.name,
                    "branch": branch,
                    "sync_state": SYNC_STATE_RU.get(state, state),
                    "local_date": get_local_last_commit_date(repository),
                    "remote_date": get_remote_last_commit_date(repository, branch),
                    "version": metadata.version,
                    "status": metadata.status,
                    "description": metadata.description,
                    "path": str(repository),
                }
            )
        return rows

    @staticmethod
    def operation_commands(operation: str, commit_message: str = "") -> list[list[str]]:
        operations = {
            "fetch": [["fetch", "--prune"]],
            "pull": [["pull"]],
            "push": [["push"]],
            "history": [["log", "-20", "--date=short", "--pretty=format:%h | %ad | %an | %s"]],
        }
        if operation == "commit":
            message = commit_message.strip()
            if not message:
                raise ValueError("Сообщение Commit не может быть пустым.")
            return [["add", "-A"], ["commit", "-m", message]]
        try:
            return operations[operation]
        except KeyError as error:
            raise ValueError(f"Неизвестная Git-операция: {operation}") from error
