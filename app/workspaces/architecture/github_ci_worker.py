from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.workspaces.architecture.github_ci import GitHubCIArtifactClient


class GitHubCIHistoryWorker(QThread):
    """Загружает историю Architecture Quality Gate без блокировки GUI."""

    completed = Signal(int, str)
    failed = Signal(str)

    def __init__(
        self,
        client: GitHubCIArtifactClient,
        repository: str,
        destination: Path,
        limit: int = 20,
    ) -> None:
        super().__init__()
        self.client = client
        self.repository = repository
        self.destination = destination
        self.limit = limit

    def run(self) -> None:
        try:
            count = self.client.download_quality_gate_history(
                self.repository,
                self.destination,
                self.limit,
            )
        except Exception as error:  # noqa: BLE001 - передаём ошибку в GUI-поток
            self.failed.emit(str(error))
            return
        self.completed.emit(count, str(self.destination))
