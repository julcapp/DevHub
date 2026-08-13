from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.workspaces.architecture.baseline import ArchitectureBaselineStore
from app.workspaces.architecture.controller import ArchitectureWorkspaceController
from app.workspaces.architecture.quality_gate import QualityGate


def run_quality_gate(project: Path) -> tuple[int, dict[str, object]]:
    root = project.resolve()
    summary = ArchitectureWorkspaceController().analyze(root)
    baseline_store = ArchitectureBaselineStore()
    gate = QualityGate()
    baseline = baseline_store.load(root)
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
    }
    return (0 if result.passed else 2), payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DevHub Architecture Quality Gate")
    parser.add_argument("project", nargs="?", default=".", help="Путь к анализируемому проекту")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Вывести результат в JSON")
    args = parser.parse_args(argv)
    code, payload = run_quality_gate(Path(args.project))
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"DevHub Quality Gate: {payload['quality_gate']}")
        print(f"Здоровье архитектуры: {payload['health_level']} ({payload['health_score']}/100)")
        for violation in payload["violations"]:
            print(f"- {violation}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
