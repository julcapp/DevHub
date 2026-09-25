from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.workspaces.architecture.baseline import ArchitectureBaseline
from app.workspaces.architecture.controller import ArchitectureSummary


@dataclass(frozen=True)
class QualityGateConfig:
    max_health_drop: int = 0
    max_new_cycles: int = 0
    max_new_high_risk_modules: int = 0
    max_coupling_growth: int = 0


@dataclass(frozen=True)
class QualityGateResult:
    passed: bool
    violations: tuple[str, ...]


class QualityGate:
    """Оценивает отклонения архитектуры от baseline по настраиваемым порогам."""

    def path_for(self, root: Path) -> Path:
        return root.resolve() / ".devhub" / "quality-gate.json"

    def load_config(self, root: Path) -> QualityGateConfig:
        path = self.path_for(root)
        if not path.exists():
            return QualityGateConfig()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return QualityGateConfig(**{k: int(payload.get(k, getattr(QualityGateConfig(), k))) for k in QualityGateConfig.__dataclass_fields__})
        except (json.JSONDecodeError, TypeError, ValueError):
            return QualityGateConfig()

    def save_config(self, root: Path, config: QualityGateConfig) -> None:
        path = self.path_for(root); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")

    def evaluate(self, baseline: ArchitectureBaseline | None, summary: ArchitectureSummary, config: QualityGateConfig) -> QualityGateResult:
        if baseline is None:
            return QualityGateResult(True, ("Эталон архитектуры не зафиксирован",))
        violations: list[str] = []
        health_drop = baseline.health_score - summary.health_score
        if health_drop > config.max_health_drop:
            violations.append(f"Падение здоровья {health_drop} превышает допустимое {config.max_health_drop}")
        new_cycles = set(summary.cycles) - set(baseline.cycles)
        if len(new_cycles) > config.max_new_cycles:
            violations.append(f"Новых циклов {len(new_cycles)} > допустимых {config.max_new_cycles}")
        old_high = set(baseline.high_risk_modules)
        new_high = {item.name for item in summary.module_details if item.risk_level == "Высокий"} - old_high
        if len(new_high) > config.max_new_high_risk_modules:
            violations.append(f"Новых модулей высокого риска {len(new_high)} > допустимых {config.max_new_high_risk_modules}")
        current = {item.name: item.coupling for item in summary.module_details}
        max_growth = max((current[name] - baseline.module_coupling.get(name, current[name]) for name in current), default=0)
        if max_growth > config.max_coupling_growth:
            violations.append(f"Рост связанности {max_growth} > допустимого {config.max_coupling_growth}")
        return QualityGateResult(not violations, tuple(violations))
