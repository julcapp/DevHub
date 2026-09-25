import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.workspaces.architecture.quality_gate import QualityGateConfig
from app.workspaces.architecture.quality_gate_dialog import QualityGateConfigDialog


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_quality_gate_dialog_reads_and_returns_thresholds() -> None:
    _app()
    dialog = QualityGateConfigDialog(QualityGateConfig(5, 1, 2, 3))

    assert dialog.health_drop.value() == 5
    assert dialog.new_cycles.value() == 1
    assert dialog.new_high_risk.value() == 2
    assert dialog.coupling_growth.value() == 3

    dialog.health_drop.setValue(8)
    dialog.new_cycles.setValue(4)
    config = dialog.config()

    assert config.max_health_drop == 8
    assert config.max_new_cycles == 4
    assert config.max_new_high_risk_modules == 2
    assert config.max_coupling_growth == 3
