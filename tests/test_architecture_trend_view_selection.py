from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from app.workspaces.architecture.analytics import ArchitectureRunRecord
from app.workspaces.architecture.trend_view import ArchitectureTrendView


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _record(run_id: str, health: int) -> ArchitectureRunRecord:
    return ArchitectureRunRecord(
        source=f"{run_id}.json",
        schema_version=1,
        project="demo",
        health_score=health,
        health_level="Хорошее",
        quality_gate="PASS",
        cycles=0,
        high_risk_modules=(),
        run_id=run_id,
    )


def test_trend_view_selects_nearest_run_on_click() -> None:
    _app()
    view = ArchitectureTrendView()
    view.resize(500, 180)
    records = (_record("100", 70), _record("101", 80), _record("102", 90))
    view.set_records(records)
    selected: list[ArchitectureRunRecord] = []
    view.record_selected.connect(selected.append)

    area = view._chart_rect()
    point = QPoint(int(area.center().x()), int(area.center().y()))
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        point,
        point,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    view.mousePressEvent(event)

    assert view.selected_index == 1
    assert selected == [records[1]]
