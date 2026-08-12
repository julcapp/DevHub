from pathlib import Path

from app.workspaces.architecture.controller import ArchitectureSummary, ModuleArchitecture
from app.workspaces.architecture.history import ArchitectureHistoryStore


def _summary(score: int, level: str, *, coupling: int = 0, high: bool = False, cycles=()) -> ArchitectureSummary:
    risk_level = "Высокий" if high else "Низкий"
    module = ModuleArchitecture("app.core", "app/core.py", (), (), (), coupling, 70 if high else 10, risk_level)
    return ArchitectureSummary(
        project_name="demo", project_path="/demo", files=1, folders=1,
        modules=1, classes=0, methods=0, functions=0, imports=0,
        internal_dependencies=0, nodes_total=2, edges_total=1,
        dependencies=(), module_details=(module,), cycles=cycles, warnings=(),
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


def test_history_compare_reports_cycles_risk_and_coupling_changes(tmp_path: Path) -> None:
    store = ArchitectureHistoryStore()
    previous = store.append(tmp_path, _summary(90, "Хорошее", coupling=1))
    current = store.append(
        tmp_path,
        _summary(65, "Требует внимания", coupling=4, high=True, cycles=(("app.core", "app.other"),)),
    )
    delta = store.compare(previous, current)
    assert delta.health_delta == -25
    assert delta.added_cycles == ("app.core → app.other → app.core",)
    assert delta.new_high_risk_modules == ("app.core",)
    assert delta.resolved_high_risk_modules == ()
    assert delta.coupling_changes == ("app.core: 1 → 4 (+3)",)


def test_history_loads_legacy_snapshot_without_detail_fields(tmp_path: Path) -> None:
    path = ArchitectureHistoryStore().path_for(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text('{"timestamp":"2026-01-01T00:00:00+00:00","health_score":80,"health_level":"Хорошее","modules":1,"cycles":0,"warnings":0,"high_risk_modules":0}\n', encoding="utf-8")
    snapshot = ArchitectureHistoryStore().load(tmp_path)[0]
    assert snapshot.cycle_chains == ()
    assert snapshot.high_risk_names == ()
    assert snapshot.coupling_by_module == {}
