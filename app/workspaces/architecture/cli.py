from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.workspaces.architecture.baseline import ArchitectureBaseline, ArchitectureBaselineStore
from app.workspaces.architecture.controller import ArchitectureSummary, ArchitectureWorkspaceController
from app.workspaces.architecture.quality_gate import QualityGate, QualityGateResult
from app.workspaces.architecture.report import build_report


def _baseline_from_summary(summary: ArchitectureSummary) -> ArchitectureBaseline:
    return ArchitectureBaseline(
        timestamp="ci-base",
        health_score=summary.health_score,
        cycles=summary.cycles,
        high_risk_modules=tuple(sorted(item.name for item in summary.module_details if item.risk_level == "Высокий")),
        module_coupling={item.name: item.coupling for item in summary.module_details},
    )


def _supports_architecture_gate(project: Path) -> bool:
    return (project.resolve() / "app" / "workspaces" / "architecture" / "quality_gate.py").exists()


def run_quality_gate(
    project: Path,
    baseline_project: Path | None = None,
    bootstrap_if_missing_gate: bool = False,
) -> tuple[int, dict[str, object], str]:
    root = project.resolve()
    summary = ArchitectureWorkspaceController().analyze(root)
    gate = QualityGate()
    baseline_summary: ArchitectureSummary | None = None

    if baseline_project is not None:
        baseline_root = baseline_project.resolve()
        if bootstrap_if_missing_gate and not _supports_architecture_gate(baseline_root):
            payload: dict[str, object] = {
                "schema_version": 1,
                "project": summary.project_name,
                "health_score": summary.health_score,
                "health_level": summary.health_level,
                "quality_gate": "BOOTSTRAP",
                "violations": [],
                "cycles": len(summary.cycles),
                "high_risk_modules": [item.name for item in summary.module_details if item.risk_level == "Высокий"],
                "baseline_source": str(baseline_root),
                "message": "Базовая ветка ещё не содержит Architecture Quality Gate; текущий PR формирует исходный baseline.",
            }
            report = build_report(summary, None, QualityGateResult(True, ()))
            return 0, payload, report.markdown
        baseline_summary = ArchitectureWorkspaceController().analyze(baseline_root)
        baseline = _baseline_from_summary(baseline_summary)
        baseline_source = str(baseline_root)
    else:
        baseline = ArchitectureBaselineStore().load(root)
        baseline_source = "project baseline file" if baseline is not None else "none"

    config = gate.load_config(root)
    result = gate.evaluate(baseline, summary, config)
    payload = {
        "schema_version": 1,
        "project": summary.project_name,
        "health_score": summary.health_score,
        "health_level": summary.health_level,
        "quality_gate": "PASS" if result.passed else "FAIL",
        "violations": list(result.violations),
        "cycles": len(summary.cycles),
        "high_risk_modules": [item.name for item in summary.module_details if item.risk_level == "Высокий"],
        "baseline_source": baseline_source,
    }
    report = build_report(summary, baseline_summary, result)
    return (0 if result.passed else 2), payload, report.markdown


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DevHub Architecture Quality Gate")
    parser.add_argument("project", nargs="?", default=".", help="Путь к анализируемому проекту")
    parser.add_argument("--baseline-project", help="Путь к checkout базовой ветки для сравнения в CI")
    parser.add_argument("--bootstrap-if-missing-gate", action="store_true", help="Не блокировать первый PR, который внедряет Architecture Quality Gate")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Вывести результат в JSON")
    parser.add_argument("--json-output", help="Сохранить машинно-читаемый JSON-результат в файл")
    parser.add_argument("--markdown-output", help="Сохранить Markdown-отчёт в файл")
    args = parser.parse_args(argv)
    baseline_project = Path(args.baseline_project) if args.baseline_project else None
    code, payload, markdown = run_quality_gate(Path(args.project), baseline_project, args.bootstrap_if_missing_gate)
    if args.markdown_output:
        output = Path(args.markdown_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
    if args.json_output:
        _write_json(Path(args.json_output), payload)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"DevHub Quality Gate: {payload['quality_gate']}")
        print(f"Здоровье архитектуры: {payload['health_level']} ({payload['health_score']}/100)")
        print(f"Baseline: {payload['baseline_source']}")
        if payload.get("message"):
            print(payload["message"])
        for violation in payload["violations"]:
            print(f"- {violation}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
