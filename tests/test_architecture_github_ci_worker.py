from pathlib import Path

from app.workspaces.architecture.github_ci_worker import GitHubCIHistoryWorker


class FakeClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def download_quality_gate_history(self, repository: str, destination: Path, limit: int = 20) -> int:
        if self.fail:
            raise RuntimeError("boom")
        destination.mkdir(parents=True, exist_ok=True)
        return 3


def test_worker_run_emits_completed_without_thread_event_loop(tmp_path: Path) -> None:
    worker = GitHubCIHistoryWorker(FakeClient(), "julcapp/DevHub", tmp_path)  # type: ignore[arg-type]
    result: list[tuple[int, str]] = []
    worker.completed.connect(lambda count, path: result.append((count, path)))
    worker.run()
    assert result == [(3, str(tmp_path))]


def test_worker_run_emits_failed_without_thread_event_loop(tmp_path: Path) -> None:
    worker = GitHubCIHistoryWorker(FakeClient(fail=True), "julcapp/DevHub", tmp_path)  # type: ignore[arg-type]
    errors: list[str] = []
    worker.failed.connect(errors.append)
    worker.run()
    assert errors == ["boom"]
