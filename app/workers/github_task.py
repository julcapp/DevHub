from PySide6.QtCore import QThread, Signal

from app.providers.github_provider import GitHubProvider, GitHubStats


class GitHubTask(QThread):
    progress = Signal(str)
    finished_success = Signal(object)
    finished_error = Signal(str)

    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.username = username.strip()

    def run(self):
        try:
            if not self.username:
                self.finished_error.emit("GitHub username не указан в настройках DevHub.")
                return

            self.progress.emit(f"GitHub: получение статистики пользователя {self.username}...")
            provider = GitHubProvider(self.username)
            stats: GitHubStats = provider.get_stats()
            self.progress.emit(
                f"GitHub: repositories={stats.repositories}, stars={stats.stars}"
            )
            self.finished_success.emit(stats)

        except Exception as error:
            self.finished_error.emit(str(error))
