import json
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.workspaces.architecture.workspace import ArchitectureWorkspace


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_workspace_updates_trend_graph_from_ci_history(tmp_path: Path) -> None:
    _app()
    for index, (score, risks) in enumerate(((70, ["app.a", "app.b"]), (82, ["app.a"])), start=1):
        (tmp_path / f"{index}.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "project": "demo",
                    "health_score": score,
                    "health_level": "Хорошее",
                    "quality_gate": "PASS",
                    "cycles": 0,
                    "high_risk_modules": risks,
                    "run_id": str(index),
                }
            ),
            encoding="utf-8",
        )

    workspace = ArchitectureWorkspace()
    workspace.ci_results_path = tmp_path
    workspace._show_ci_trend()

    assert len(workspace.ci_trend_graph.records) == 2
    assert [item.health_score for item in workspace.ci_trend_graph.records] == [70, 82]
    assert [len(item.high_risk_modules) for item in workspace.ci_trend_graph.records] == [2, 1]


def test_workspace_clears_trend_graph_when_ci_history_is_empty(tmp_path: Path) -> None:
    _app()
    workspace = ArchitectureWorkspace()
    workspace.ci_results_path = tmp_path
    workspace._show_ci_trend()
    assert workspace.ci_trend_graph.records == ()
