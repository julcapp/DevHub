from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.workspaces.architecture.baseline import ArchitectureBaseline, ArchitectureBaselineStore
from app.workspaces.architecture.controller import ArchitectureSummary, ArchitectureWorkspaceController
from app.workspaces.architecture.quality_gate import QualityGate


def _baseline_from_summary(summary: ArchitectureSummary) -> ArchitectureBaseline:
    return ArchitectureBaseline(
        timestamp="ci-base",
        health_score=summary.health_score,
        cycles=summary.cycles,
        high_risk_modules=tuple(sorted(item.name for item in summary.module_details if item.risk_level == "Высокий")),
        module_coupling={item.name: item.coupling for item in summary.module_details},
    )


def run_quality_gate(project: Path, baseline_project: Path | None = None) -> tuple[int, dict[str, object]]:
    root = project.resolve()
    controller = ArchitectureWorkspaceController()
    summary = controller.analyze(root)
    gate = QualityGate()

    if baseline_project is not None:
        baseline_summary = ArchitectureWorkspaceController().analyze(baseline_project.resolve())
        baseline = _baseline_from_summary(baseline_summary)
        baseline_source = str(baseline_project.resolve())
    else:
        baseline = ArchitectureBaselineStore().load(root)
        baseline_source = "project baseline file" if baseline is not None else "none"

    config = gate.load_config(root)
    result = gate.evaluate(baseline, summary, config)
    payload: dict[str, object] = {
        "project": summary.project_name,
        "health_score": summary.health_score,
        "health_level": summary.health_level,
        "quality_gate": "PASS" if result.passed else "FAIL",
        "violations": list(result.violations),
        "cycles": len(summary.cycles),
        "high_risk_modules": [item.name for item in summary.module_details if item.risk_level == "Высокий"],
        "baseline_source": baseline_source,
    }
    return (0 if result.passed else 2), payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DevHub Architecture Quality Gate")
    parser.add_argument("project", nargs="?", default=".", help="Путь к анализируемому проекту")
    parser.add_argument("--baseline-project", help="Путь к checkout базовой ветки для сравнения в CI")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Вывести результат в JSON")
    args = parser.parse_args(argv)
    baseline_project = Path(args.baseline_project) if args.baseline_project else None
    code, payload = run_quality_gate(Path(args.project), baseline_project)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"DevHub Quality Gate: {payload['quality_gate']}")
        print(f"Здоровье архитектуры: {payload['health_level']} ({payload['health_score']}/100)")
        print(f"Baseline: {payload['baseline_source']}")
        for violation in payload["violations"]:
            print(f"- {violation}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
