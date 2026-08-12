from pathlib import Path

from app.workspaces.architecture.controller import ArchitectureSummary, ModuleArchitecture
from app.workspaces.architecture.history import ArchitectureHistoryStore


def _summary(score: int, level: str) -> ArchitectureSummary:
    module = ModuleArchitecture("app.core", "app/core.py", (), (), (), 0, 10, "Низкий")
    return ArchitectureSummary(
        project_name="demo", project_path="/demo", files=1, folders=1,
        modules=1, classes=0, methods=0, functions=0, imports=0,
        internal_dependencies=0, nodes_total=2, edges_total=1,
        dependencies=(), module_details=(module,), cycles=(), warnings=(),
        top_risks=(module,), health_score=score, health_level=level,
    )


def test_history_store_appends_and_loads_snapshots(tmp_path: Path) -> None:
    store = ArchitectureHistoryStore()
    store.append(tmp_path, _summary(90, "Хорошее"))
    store.append(tmp_path, _summary(82, "Хорошее"))

    history = store.load(tmp_path)

    assert [item.health_score for item in history] == [90, 82]
    assert store.path_for(tmp_path).exists()
    assert store.trend(history) == "Ухудшение -8"


def test_history_trend_reports_improvement_and_insufficient_data(tmp_path: Path) -> None:
    store = ArchitectureHistoryStore()
    first = store.append(tmp_path, _summary(60, "Требует внимания"))
    assert store.trend((first,)) == "Недостаточно данных"
    second = store.append(tmp_path, _summary(75, "Требует внимания"))
    assert store.trend((first, second)) == "Улучшение +15"
