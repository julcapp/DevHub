from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.workspaces.architecture.controller import ArchitectureSummary


@dataclass(frozen=True)
class ArchitectureSnapshot:
    timestamp: str
    health_score: int
    health_level: str
    modules: int
    cycles: int
    warnings: int
    high_risk_modules: int
    cycle_chains: tuple[str, ...] = ()
    high_risk_names: tuple[str, ...] = ()
    coupling_by_module: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ArchitectureDelta:
    health_delta: int
    added_cycles: tuple[str, ...]
    removed_cycles: tuple[str, ...]
    new_high_risk_modules: tuple[str, ...]
    resolved_high_risk_modules: tuple[str, ...]
    coupling_changes: tuple[str, ...]


class ArchitectureHistoryStore:
    """Хранит историю архитектурных анализов проекта в .devhub/architecture-history.jsonl."""

    def path_for(self, root: Path) -> Path:
        return root.resolve() / ".devhub" / "architecture-history.jsonl"

    def append(self, root: Path, summary: ArchitectureSummary) -> ArchitectureSnapshot:
        snapshot = ArchitectureSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            health_score=summary.health_score,
            health_level=summary.health_level,
            modules=summary.modules,
            cycles=len(summary.cycles),
            warnings=len(summary.warnings),
            high_risk_modules=sum(1 for item in summary.module_details if item.risk_level == "Высокий"),
            cycle_chains=tuple(" → ".join((*cycle, cycle[0])) for cycle in summary.cycles),
            high_risk_names=tuple(sorted(item.name for item in summary.module_details if item.risk_level == "Высокий")),
            coupling_by_module={item.name: item.coupling for item in summary.module_details},
        )
        path = self.path_for(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(snapshot), ensure_ascii=False) + "\n")
        return snapshot

    def load(self, root: Path, limit: int = 20) -> tuple[ArchitectureSnapshot, ...]:
        path = self.path_for(root)
        if not path.exists():
            return ()
        snapshots: list[ArchitectureSnapshot] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                payload["cycle_chains"] = tuple(payload.get("cycle_chains", ()))
                payload["high_risk_names"] = tuple(payload.get("high_risk_names", ()))
                payload["coupling_by_module"] = dict(payload.get("coupling_by_module", {}))
                snapshots.append(ArchitectureSnapshot(**payload))
            except (json.JSONDecodeError, TypeError):
                continue
        return tuple(snapshots[-max(limit, 0):])

    @staticmethod
    def trend(history: tuple[ArchitectureSnapshot, ...]) -> str:
        if len(history) < 2:
            return "Недостаточно данных"
        delta = history[-1].health_score - history[-2].health_score
        if delta > 0:
            return f"Улучшение +{delta}"
        if delta < 0:
            return f"Ухудшение {delta}"
        return "Без изменений"

    @staticmethod
    def compare(previous: ArchitectureSnapshot, current: ArchitectureSnapshot) -> ArchitectureDelta:
        previous_cycles, current_cycles = set(previous.cycle_chains), set(current.cycle_chains)
        previous_high, current_high = set(previous.high_risk_names), set(current.high_risk_names)
        coupling_changes: list[str] = []
        for name in sorted(set(previous.coupling_by_module) | set(current.coupling_by_module)):
            before = previous.coupling_by_module.get(name)
            after = current.coupling_by_module.get(name)
            if before is None:
                coupling_changes.append(f"{name}: новый модуль, связанность {after}")
            elif after is None:
                coupling_changes.append(f"{name}: модуль удалён (было {before})")
            elif before != after:
                sign = "+" if after - before > 0 else ""
                coupling_changes.append(f"{name}: {before} → {after} ({sign}{after - before})")
        return ArchitectureDelta(
            health_delta=current.health_score - previous.health_score,
            added_cycles=tuple(sorted(current_cycles - previous_cycles)),
            removed_cycles=tuple(sorted(previous_cycles - current_cycles)),
            new_high_risk_modules=tuple(sorted(current_high - previous_high)),
            resolved_high_risk_modules=tuple(sorted(previous_high - current_high)),
            coupling_changes=tuple(coupling_changes),
        )
