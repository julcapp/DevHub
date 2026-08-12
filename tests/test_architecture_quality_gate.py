from pathlib import Path

from app.workspaces.architecture.baseline import ArchitectureBaseline
from app.workspaces.architecture.controller import ArchitectureSummary, ModuleArchitecture
from app.workspaces.architecture.quality_gate import QualityGate, QualityGateConfig


def _summary(score: int, coupling: int, high: bool = False, cycles=()) -> ArchitectureSummary:
    module = ModuleArchitecture("app.core", "app/core.py", (), (), (), coupling, 70 if high else 10, "Высокий" if high else "Низкий")
    return ArchitectureSummary("demo", "/demo", 1, 1, 1, 0, 0, 0, 0, 0, 2, 1, (), (module,), cycles, (), (module,), score, "Хорошее")


def _baseline() -> ArchitectureBaseline:
    return ArchitectureBaseline("now", 90, (), (), {"app.core": 1})


def test_quality_gate_fails_on_strict_defaults() -> None:
    result = QualityGate().evaluate(_baseline(), _summary(80, 3, True), QualityGateConfig())
    assert result.passed is False
    assert any("Падение здоровья" in item for item in result.violations)
    assert any("высокого риска" in item for item in result.violations)
    assert any("Рост связанности" in item for item in result.violations)


def test_quality_gate_allows_configured_tolerance(tmp_path: Path) -> None:
    gate = QualityGate(); config = QualityGateConfig(15, 1, 1, 3); gate.save_config(tmp_path, config)
    loaded = gate.load_config(tmp_path)
    result = gate.evaluate(_baseline(), _summary(80, 3, True), loaded)
    assert loaded == config
    assert result.passed is True
    assert result.violations == ()
