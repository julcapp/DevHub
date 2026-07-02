from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.git_manager import run_repository_command


class GitTask(QThread):
    progress = Signal(str)
    finished_success = Signal(object)
    finished_error = Signal(str)

    def __init__(self, repo_path: Path, command: list[str], parent=None):
        super().__init__(parent)
        self.repo_path = repo_path
        self.command = command

    def run(self):
        try:
            command_text = "git " + " ".join(self.command)
            self.progress.emit(f"Запущена команда: {command_text}")

            result = run_repository_command(self.repo_path, self.command)

            self.progress.emit(f"Команда завершена: {command_text} [{result.status}]")
            self.finished_success.emit(result)

        except Exception as error:
            self.finished_error.emit(str(error))