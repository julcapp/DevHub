import json
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.workspaces.architecture.github_ci_worker import GitHubCIHistoryWorker
from app.workspaces.architecture.workspace import ArchitectureWorkspace


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_workspace_refreshes_ci_history_from_github(tmp_path: Path, monkeypatch) -> None:
    _app()
    git = tmp_path / ".git"; git.mkdir()
    (git / "config").write_text('[remote "origin"]\n    url = https://github.com/julcapp/DevHub.git\n', encoding="utf-8")
    workspace = ArchitectureWorkspace(); workspace.root_path = tmp_path

    class FakeClient:
        def download_quality_gate_history(self, repository: str, destination: Path, limit: int = 20) -> int:
            assert repository == "julcapp/DevHub"
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "123.json").write_text(json.dumps({"schema_version":1,"project":"demo","health_score":90,"health_level":"Хорошее","quality_gate":"PASS","cycles":0,"high_risk_modules":[],"run_id":"123","commit_sha":"abcdef123456"}), encoding="utf-8")
            return 1

    workspace.github_ci = FakeClient()  # type: ignore[assignment]

    def run_immediately(self: GitHubCIHistoryWorker) -> None:
        self.run()

    monkeypatch.setattr(GitHubCIHistoryWorker, "start", run_immediately)
    workspace.refresh_ci_from_github()
    assert "загружено 1 результатов" in workspace.status_label.text()
    assert "PASS 1" in workspace.ci_trend_label.text()
    assert workspace.ci_trend_list.count() == 1


def test_workspace_requires_project_before_github_refresh() -> None:
    _app(); workspace = ArchitectureWorkspace(); workspace.refresh_ci_from_github()
    assert workspace.status_label.text() == "Сначала выберите проект."
