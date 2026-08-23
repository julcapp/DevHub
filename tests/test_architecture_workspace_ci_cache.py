import json
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.workspaces.architecture.workspace import ArchitectureWorkspace


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_workspace_shows_ci_cache_status(tmp_path: Path) -> None:
    _app()
    workspace = ArchitectureWorkspace()
    workspace.root_path = tmp_path
    cache = tmp_path / ".devhub" / "ci-quality-gate"
    cache.mkdir(parents=True)
    (cache / "100.json").write_text(json.dumps({"schema_version":1,"project":"demo","health_score":80,"health_level":"Хорошее","quality_gate":"PASS","cycles":0,"high_risk_modules":[]}), encoding="utf-8")
    workspace.ci_cache.maintain(cache)
    workspace.ci_results_path = cache
    workspace._show_ci_trend()
    assert "сохранено 1 запусков" in workspace.ci_cache_label.text()
    assert "лимит 50" in workspace.ci_cache_label.text()


def test_workspace_clears_ci_cache(tmp_path: Path) -> None:
    _app()
    workspace = ArchitectureWorkspace()
    workspace.root_path = tmp_path
    cache = tmp_path / ".devhub" / "ci-quality-gate"
    cache.mkdir(parents=True)
    for run_id in (100, 101):
        (cache / f"{run_id}.json").write_text(json.dumps({"schema_version":1,"project":"demo","health_score":80,"health_level":"Хорошее","quality_gate":"PASS","cycles":0,"high_risk_modules":[]}), encoding="utf-8")
    workspace.ci_cache.maintain(cache)
    workspace.ci_results_path = cache
    workspace.clear_ci_cache()
    assert "удалено 2 результатов" in workspace.status_label.text()
    assert workspace.ci_trend_label.text() == "CI Architecture Trend: данных нет"
    assert "0 запусков" in workspace.ci_cache_label.text()
