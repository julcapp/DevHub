from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEventLoop, QThread
from PySide6.QtWidgets import QApplication

from app.services.session_service import SessionService, WorkspaceSession


ProgressCallback = Callable[[str, int], None]


@dataclass(slots=True)
class ShutdownReport:
    started_at: datetime
    finished_at: datetime | None = None
    forced_tasks: int = 0


class ApplicationLifecycleManager:
    """Coordinates startup, session persistence and deterministic shutdown."""

    def __init__(self, window, session_service: SessionService | None = None) -> None:
        self.window = window
        self.session_service = session_service or SessionService()
        self.session = WorkspaceSession()
        self.shutdown_started = False
        self.accept_new_tasks = True

    def startup(self) -> WorkspaceSession:
        self.session = self.session_service.mark_startup()
        self.restore_window_state()
        return self.session

    def restore_window_state(self) -> None:
        geometry = self.session_service.decode_qt_state(self.session.geometry)
        state = self.session_service.decode_qt_state(self.session.window_state)
        if not geometry.isEmpty():
            self.window.restoreGeometry(geometry)
        if not state.isEmpty():
            self.window.restoreState(state)

    def capture_window_state(self) -> WorkspaceSession:
        self.session.geometry = self.session_service.encode_qt_state(self.window.saveGeometry())
        self.session.window_state = self.session_service.encode_qt_state(self.window.saveState())
        selected_repo = getattr(self.window, "selected_repo", None)
        self.session.selected_repository = str(selected_repo) if selected_repo else ""
        return self.session

    def can_start_task(self) -> bool:
        return self.accept_new_tasks and not self.shutdown_started

    def _yield_ui(self) -> None:
        QCoreApplication.processEvents(QEventLoop.AllEvents, 50)

    def _stop_thread(self, task: QThread | None, timeout_ms: int = 3000) -> bool:
        if task is None or not task.isRunning():
            return False
        task.requestInterruption()
        task.quit()
        if task.wait(timeout_ms):
            return False
        task.terminate()
        task.wait(1000)
        return True

    def shutdown(self, progress: ProgressCallback | None = None) -> ShutdownReport:
        if self.shutdown_started:
            return ShutdownReport(started_at=datetime.now(timezone.utc), finished_at=datetime.now(timezone.utc))

        self.shutdown_started = True
        self.accept_new_tasks = False
        report = ShutdownReport(started_at=datetime.now(timezone.utc))

        def step(text: str, value: int) -> None:
            if progress:
                progress(text, value)
            self._yield_ui()

        step("Блокировка новых операций", 10)
        runtime_timer = getattr(self.window, "runtime_timer", None)
        if runtime_timer is not None:
            runtime_timer.stop()

        step("Сохранение рабочего пространства", 25)
        self.capture_window_state()
        self.session_service.save(self.session)

        step("Завершение Git-задач", 40)
        report.forced_tasks += int(self._stop_thread(getattr(self.window, "current_git_task", None)))

        step("Завершение GitHub-задач", 55)
        report.forced_tasks += int(self._stop_thread(getattr(self.window, "current_github_task", None)))

        step("Закрытие дочерних окон", 70)
        for attribute_name in (
            "devadvisor_window",
            "research_evolution_window",
            "engineering_intelligence_window",
        ):
            child = getattr(self.window, attribute_name, None)
            if child is not None:
                child.close()

        step("Закрытие соединений и освобождение ресурсов", 85)
        engine = getattr(self.window, "db_engine", None)
        if engine is not None:
            engine.dispose()

        step("Фиксация корректного завершения", 95)
        self.session_service.mark_clean_shutdown(self.session)
        self._write_shutdown_log(report)

        report.finished_at = datetime.now(timezone.utc)
        step("Работа DevHub завершена", 100)
        return report

    def _write_shutdown_log(self, report: ShutdownReport) -> None:
        log_path = Path("logs") / "lifecycle.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        line = (
            f"{datetime.now(timezone.utc).isoformat()} | clean_shutdown | "
            f"forced_tasks={report.forced_tasks}\n"
        )
        with log_path.open("a", encoding="utf-8") as stream:
            stream.write(line)

    @staticmethod
    def quit_application() -> None:
        app = QApplication.instance()
        if app is not None:
            app.quit()
