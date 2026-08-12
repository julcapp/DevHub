from __future__ import annotations

import json
from dataclasses import asdict, dataclass
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
