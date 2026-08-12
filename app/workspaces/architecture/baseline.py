from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.workspaces.architecture.controller import ArchitectureSummary


@dataclass(frozen=True)
class ArchitectureBaseline:
    timestamp: str
    health_score: int
    cycles: tuple[tuple[str, ...], ...]
    high_risk_modules: tuple[str, ...]
    module_coupling: dict[str, int]


class ArchitectureBaselineStore:
    """Хранит эталон архитектуры и сравнивает текущий анализ с ним."""

    def path_for(self, root: Path) -> Path:
        return root.resolve() / ".devhub" / "architecture-baseline.json"

    def save(self, root: Path, summary: ArchitectureSummary) -> ArchitectureBaseline:
        baseline = ArchitectureBaseline(
            timestamp=datetime.now(timezone.utc).isoformat(),
            health_score=summary.health_score,
            cycles=summary.cycles,
            high_risk_modules=tuple(sorted(item.name for item in summary.module_details if item.risk_level == "Высокий")),
            module_coupling={item.name: item.coupling for item in summary.module_details},
        )
        path = self.path_for(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(baseline), ensure_ascii=False, indent=2), encoding="utf-8")
        return baseline

    def load(self, root: Path) -> ArchitectureBaseline | None:
        path = self.path_for(root)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["cycles"] = tuple(tuple(cycle) for cycle in payload.get("cycles", ()))
            payload["high_risk_modules"] = tuple(payload.get("high_risk_modules", ()))
            payload["module_coupling"] = dict(payload.get("module_coupling", {}))
            return ArchitectureBaseline(**payload)
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    @staticmethod
    def compare(baseline: ArchitectureBaseline | None, summary: ArchitectureSummary) -> tuple[str, ...]:
        if baseline is None:
            return ("Эталон архитектуры не зафиксирован",)
        changes: list[str] = []
        delta = summary.health_score - baseline.health_score
        if delta:
            changes.append(f"Здоровье относительно эталона: {delta:+d}")
        old_cycles = set(baseline.cycles); new_cycles = set(summary.cycles)
        for cycle in sorted(new_cycles - old_cycles): changes.append(f"Новый цикл относительно эталона: {' → '.join((*cycle, cycle[0]))}")
        old_high = set(baseline.high_risk_modules); new_high = {item.name for item in summary.module_details if item.risk_level == "Высокий"}
        for name in sorted(new_high - old_high): changes.append(f"Новый высокий риск относительно эталона: {name}")
        current = {item.name: item.coupling for item in summary.module_details}
        for name in sorted(set(current) & set(baseline.module_coupling)):
            diff = current[name] - baseline.module_coupling[name]
            if diff > 0: changes.append(f"Связанность выше эталона: {name}: {baseline.module_coupling[name]} → {current[name]} (+{diff})")
        return tuple(changes) or ("Отклонений от архитектурного эталона не обнаружено",)
