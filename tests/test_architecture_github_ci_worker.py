import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

from app.workspaces.architecture.github_ci_worker import GitHubCIHistoryWorker


class FakeClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def download_quality_gate_history(self, repository: str, destination: Path, limit: int = 20) -> int:
        if self.fail:
            raise RuntimeError("boom")
        destination.mkdir(parents=True, exist_ok=True)
        return 3


def _wait(worker: GitHubCIHistoryWorker) -> None:
    QCoreApplication.instance() or QCoreApplication([])
    loop = QEventLoop()
    worker.finished.connect(loop.quit)
    QTimer.singleShot(3000, loop.quit)
    worker.start()
    loop.exec()
    worker.wait(1000)


def test_worker_emits_completed(tmp_path: Path) -> None:
    worker = GitHubCIHistoryWorker(FakeClient(), "julcapp/DevHub", tmp_path)  # type: ignore[arg-type]
    result: list[tuple[int, str]] = []
    worker.completed.connect(lambda count, path: result.append((count, path)))
    _wait(worker)
    assert result == [(3, str(tmp_path))]


def test_worker_emits_failed(tmp_path: Path) -> None:
    worker = GitHubCIHistoryWorker(FakeClient(fail=True), "julcapp/DevHub", tmp_path)  # type: ignore[arg-type]
    errors: list[str] = []
    worker.failed.connect(errors.append)
    _wait(worker)
    assert errors == ["boom"]
