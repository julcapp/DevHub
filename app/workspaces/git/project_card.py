from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QTextEdit

from app.git_manager import detect_sync_state, get_branch
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


class ProjectCardWidget(QTextEdit):
    """Паспорт выбранного инженерного проекта."""

    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setText("Выберите репозиторий в таблице.")

    def show_repository(self, repository: Path) -> None:
        metadata = load_project_metadata(repository)
        branch = get_branch(repository)
        sync_state = SYNC_STATE_RU.get(detect_sync_state(repository, branch), "Неизвестно")
        self.setText(
            "\n".join(
                [
                    f"Проект: {metadata.name}",
                    f"Код: {metadata.code}",
                    f"Версия: {metadata.version}",
                    f"Статус: {metadata.status}",
                    f"Приоритет: {metadata.priority}",
                    f"Тип: {metadata.project_type}",
                    f"Ветка: {branch}",
                    f"Git: {sync_state}",
                    f"Источник данных: {metadata.source}",
                    "",
                    "Описание:",
                    metadata.description,
                    "",
                    "Путь:",
                    str(repository),
                ]
            )
        )
