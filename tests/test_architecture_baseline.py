from pathlib import Path

from app.workspaces.architecture.baseline import ArchitectureBaselineStore
from app.workspaces.architecture.controller import ArchitectureSummary, ModuleArchitecture


def _summary(score: int = 90, coupling: int = 1, high: bool = False) -> ArchitectureSummary:
    module = ModuleArchitecture("app.core", "app/core.py", (), (), (), coupling, 70 if high else 10, "Высокий" if high else "Низкий")
    return ArchitectureSummary("demo", "/demo", 1, 1, 1, 0, 0, 0, 0, 0, 2, 1, (), (module,), (), (), (module,), score, "Хорошее")


def test_baseline_save_load_and_compare(tmp_path: Path) -> None:
    store = ArchitectureBaselineStore(); store.save(tmp_path, _summary())
    baseline = store.load(tmp_path)
    assert baseline is not None and baseline.health_score == 90
    assert store.compare(baseline, _summary()) == ("Отклонений от архитектурного эталона не обнаружено",)


def test_baseline_detects_regression(tmp_path: Path) -> None:
    store = ArchitectureBaselineStore(); baseline = store.save(tmp_path, _summary(90, 1, False))
    changes = store.compare(baseline, _summary(70, 4, True))
    assert "Здоровье относительно эталона: -20" in changes
    assert "Новый высокий риск относительно эталона: app.core" in changes
    assert "Связанность выше эталона: app.core: 1 → 4 (+3)" in changes
