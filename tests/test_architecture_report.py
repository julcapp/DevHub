from app.workspaces.architecture.controller import ArchitectureSummary, ModuleArchitecture
from app.workspaces.architecture.quality_gate import QualityGateResult
from app.workspaces.architecture.report import build_report


def _summary(score: int, modules: tuple[ModuleArchitecture, ...], cycles=()) -> ArchitectureSummary:
    return ArchitectureSummary(
        project_name="demo", project_path="/demo", files=2, folders=1, modules=len(modules),
        classes=0, methods=0, functions=0, imports=0, internal_dependencies=0,
        nodes_total=2, edges_total=0, dependencies=(), module_details=modules,
        cycles=cycles, health_score=score, health_level="Хорошее" if score >= 80 else "Проблемное",
    )


def test_report_prioritizes_regressions_and_improvements() -> None:
    base_module = ModuleArchitecture("app.core", "app/core.py", (), (), (), coupling=1, risk_score=10, risk_level="Низкий")
    current_module = ModuleArchitecture(
        "app.core", "app/core.py", (), (), (), coupling=3, risk_score=70, risk_level="Высокий",
        recommendations=("Разделить ответственность",),
    )
    baseline = _summary(90, (base_module,))
    current = _summary(70, (current_module,), (("app.core", "app.api"),))
    report = build_report(current, baseline, QualityGateResult(False, ("regression",)))
    assert "**CRITICAL:** Здоровье архитектуры снизилось" in report.markdown
    assert "**CRITICAL:** Новый модуль высокого риска: app.core" in report.markdown
    assert "**WARNING:** Рост связанности: app.core: 1 → 3 (+2)" in report.markdown
    assert "Разделить ответственность" in report.markdown


def test_report_marks_stable_architecture() -> None:
    module = ModuleArchitecture("app.core", "app/core.py", (), (), (), coupling=1)
    baseline = _summary(90, (module,))
    current = _summary(90, (module,))
    report = build_report(current, baseline, QualityGateResult(True, ()))
    assert "**STABLE:**" in report.markdown
