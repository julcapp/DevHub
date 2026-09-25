import json
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.workspaces.architecture.workspace import ArchitectureWorkspace


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_workspace_shows_ci_architecture_trend(tmp_path: Path) -> None:
    _app()
    (tmp_path / "001.json").write_text(json.dumps({"schema_version": 1, "project": "demo", "health_score": 70, "health_level": "Требует внимания", "quality_gate": "PASS", "cycles": 1, "high_risk_modules": ["app.a"], "run_id": "100", "commit_sha": "1234567890abcdef", "pull_request": "16"}), encoding="utf-8")
    (tmp_path / "002.json").write_text(json.dumps({"schema_version": 1, "project": "demo", "health_score": 82, "health_level": "Хорошее", "quality_gate": "PASS", "cycles": 0, "high_risk_modules": [] , "run_id": "101", "commit_sha": "abcdef1234567890", "pull_request": "16"}), encoding="utf-8")
    workspace = ArchitectureWorkspace()
    workspace.ci_results_path = tmp_path
    workspace._show_ci_trend()
    assert "70/100 → 82/100 (+12)" in workspace.ci_trend_label.text()
    assert "PASS 2" in workspace.ci_trend_label.text()
    assert workspace.ci_trend_list.count() == 2
    assert "run 101" in workspace.ci_trend_list.item(0).text()
    assert "PR #16" in workspace.ci_trend_list.item(0).text()


def test_workspace_handles_empty_ci_history(tmp_path: Path) -> None:
    _app()
    workspace = ArchitectureWorkspace()
    workspace.ci_results_path = tmp_path
    workspace._show_ci_trend()
    assert workspace.ci_trend_label.text() == "CI Architecture Trend: данных нет"
    assert workspace.ci_trend_list.item(0).text() == "JSON-результаты Quality Gate не найдены"
