from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.workspaces.architecture.analytics import ArchitectureRunRecord
from app.workspaces.architecture.trend_view import ArchitectureTrendView


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _record(run_id: str, health: int, high_risk: int) -> ArchitectureRunRecord:
    return ArchitectureRunRecord(
        source=str(Path(run_id + ".json")),
        schema_version=1,
        project="demo",
        health_score=health,
        health_level="Хорошее",
        quality_gate="PASS",
        cycles=0,
        high_risk_modules=tuple(f"module.{index}" for index in range(high_risk)),
        run_id=run_id,
    )


def test_trend_view_accepts_records() -> None:
    _app()
    view = ArchitectureTrendView()
    records = (_record("101", 70, 3), _record("102", 82, 1))
    view.set_records(records)
    assert view.records == records
    assert view.minimumHeight() >= 150


def test_trend_view_handles_empty_records() -> None:
    _app()
    view = ArchitectureTrendView()
    view.set_records(())
    assert view.records == ()
