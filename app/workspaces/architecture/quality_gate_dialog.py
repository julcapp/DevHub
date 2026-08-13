from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QSpinBox, QVBoxLayout

from app.workspaces.architecture.quality_gate import QualityGateConfig


class QualityGateConfigDialog(QDialog):
    """Редактор порогов архитектурного Quality Gate."""

    def __init__(self, config: QualityGateConfig, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Пороги Quality Gate")
        self.setModal(True)

        self.health_drop = self._spin(config.max_health_drop)
        self.new_cycles = self._spin(config.max_new_cycles)
        self.new_high_risk = self._spin(config.max_new_high_risk_modules)
        self.coupling_growth = self._spin(config.max_coupling_growth)

        form = QFormLayout()
        form.addRow("Допустимое падение здоровья:", self.health_drop)
        form.addRow("Новые циклы:", self.new_cycles)
        form.addRow("Новые модули высокого риска:", self.new_high_risk)
        form.addRow("Рост связанности модуля:", self.coupling_growth)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Значение 0 означает строгий запрет на ухудшение по соответствующему показателю."))
        layout.addLayout(form)
        layout.addWidget(buttons)

    @staticmethod
    def _spin(value: int) -> QSpinBox:
        widget = QSpinBox()
        widget.setRange(0, 1000)
        widget.setValue(max(0, int(value)))
        return widget

    def config(self) -> QualityGateConfig:
        return QualityGateConfig(
            max_health_drop=self.health_drop.value(),
            max_new_cycles=self.new_cycles.value(),
            max_new_high_risk_modules=self.new_high_risk.value(),
            max_coupling_growth=self.coupling_growth.value(),
        )
