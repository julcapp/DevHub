from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.git_manager import run_repository_command


class GitOperationTask(QThread):
    """Выполняет одну или несколько Git-команд вне UI-потока."""

    progress = Signal(str)
    result_ready = Signal(object)
    finished_success = Signal()
    finished_error = Signal(str)

    def __init__(self, repository: Path, commands: list[list[str]], parent=None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.commands = commands

    def run(self) -> None:
        try:
            for command in self.commands:
                command_text = "git " + " ".join(command)
                self.progress.emit(f"> {command_text}")
                result = run_repository_command(self.repository, command)
                self.result_ready.emit(result)
                if result.status != "SUCCESS":
                    self.finished_error.emit(
                        f"Команда завершилась с ошибкой: {command_text}"
                    )
                    return
            self.finished_success.emit()
        except Exception as error:
            self.finished_error.emit(str(error))
