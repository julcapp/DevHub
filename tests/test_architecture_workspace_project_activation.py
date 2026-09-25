import json
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.workspaces.architecture.github_ci_worker import GitHubCIHistoryWorker
from app.workspaces.architecture.workspace import ArchitectureWorkspace


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_activate_project_loads_existing_ci_cache_without_refresh(tmp_path: Path) -> None:
    _app()
    git = tmp_path / ".git"; git.mkdir()
    (git / "config").write_text('[remote "origin"]\n    url = https://github.com/julcapp/DevHub.git\n', encoding="utf-8")
    cache = tmp_path / ".devhub" / "ci-quality-gate"; cache.mkdir(parents=True)
    (cache / "100.json").write_text(json.dumps({"schema_version":1,"project":"demo","health_score":88,"health_level":"Хорошее","quality_gate":"PASS","cycles":0,"high_risk_modules":[],"run_id":"100","commit_sha":"abcdef123456"}), encoding="utf-8")
    workspace = ArchitectureWorkspace()
    workspace.activate_project(tmp_path, refresh_ci=False)
    assert workspace.root_path == tmp_path.resolve()
    assert workspace.ci_results_path == cache
    assert "PASS 1" in workspace.ci_trend_label.text()
    assert "julcapp/DevHub" in workspace.status_label.text()


def test_activate_project_auto_starts_github_refresh(tmp_path: Path, monkeypatch) -> None:
    _app()
    git = tmp_path / ".git"; git.mkdir()
    (git / "config").write_text('[remote "origin"]\n    url = https://github.com/julcapp/DevHub.git\n', encoding="utf-8")
    started: list[str] = []

    def fake_start(self: GitHubCIHistoryWorker) -> None:
        started.append(self.repository)

    monkeypatch.setattr(GitHubCIHistoryWorker, "start", fake_start)
    workspace = ArchitectureWorkspace()
    workspace.activate_project(tmp_path, refresh_ci=True)
    assert started == ["julcapp/DevHub"]
    assert not workspace.ci_refresh_button.isEnabled()


def test_activate_project_without_github_origin_keeps_local_mode(tmp_path: Path) -> None:
    _app()
    workspace = ArchitectureWorkspace()
    workspace.activate_project(tmp_path, refresh_ci=True)
    assert workspace.ci_worker is None
    assert workspace.ci_trend_label.text() == "CI Architecture Trend: кэш отсутствует"
    assert workspace.status_label.text() == "Проект открыт. GitHub origin не обнаружен."
