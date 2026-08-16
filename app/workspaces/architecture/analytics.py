from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArchitectureRunRecord:
    source: str
    schema_version: int
    project: str
    health_score: int
    health_level: str
    quality_gate: str
    cycles: int
    high_risk_modules: tuple[str, ...]
    run_id: str = ""
    commit_sha: str = ""
    pull_request: str = ""


@dataclass(frozen=True)
class ArchitectureTrend:
    runs: int
    first_health_score: int | None
    latest_health_score: int | None
    health_delta: int | None
    pass_count: int
    fail_count: int
    bootstrap_count: int
    latest_high_risk_modules: tuple[str, ...]


def load_records(root: Path) -> tuple[ArchitectureRunRecord, ...]:
    records: list[ArchitectureRunRecord] = []
    for path in sorted(root.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict) or "quality_gate" not in payload or "health_score" not in payload:
            continue
        records.append(
            ArchitectureRunRecord(
                source=str(path),
                schema_version=int(payload.get("schema_version", 1)),
                project=str(payload.get("project", "")),
                health_score=int(payload.get("health_score", 0)),
                health_level=str(payload.get("health_level", "")),
                quality_gate=str(payload.get("quality_gate", "")),
                cycles=int(payload.get("cycles", 0)),
                high_risk_modules=tuple(str(item) for item in payload.get("high_risk_modules", ())),
                run_id=str(payload.get("run_id", "")),
                commit_sha=str(payload.get("commit_sha", "")),
                pull_request=str(payload.get("pull_request", "")),
            )
        )
    return tuple(records)


def summarize(records: tuple[ArchitectureRunRecord, ...]) -> ArchitectureTrend:
    if not records:
        return ArchitectureTrend(0, None, None, None, 0, 0, 0, ())
    first = records[0]; latest = records[-1]
    return ArchitectureTrend(
        runs=len(records),
        first_health_score=first.health_score,
        latest_health_score=latest.health_score,
        health_delta=latest.health_score - first.health_score,
        pass_count=sum(item.quality_gate == "PASS" for item in records),
        fail_count=sum(item.quality_gate == "FAIL" for item in records),
        bootstrap_count=sum(item.quality_gate == "BOOTSTRAP" for item in records),
        latest_high_risk_modules=latest.high_risk_modules,
    )


def build_markdown(trend: ArchitectureTrend) -> str:
    if trend.runs == 0:
        return "# DevHub Architecture Trend\n\nДанные Quality Gate пока отсутствуют.\n"
    delta = trend.health_delta or 0
    lines = [
        "# DevHub Architecture Trend",
        "",
        f"- Запусков: {trend.runs}",
        f"- Здоровье: {trend.first_health_score}/100 → {trend.latest_health_score}/100 ({delta:+d})",
        f"- PASS: {trend.pass_count}",
        f"- FAIL: {trend.fail_count}",
        f"- BOOTSTRAP: {trend.bootstrap_count}",
        f"- High-risk модулей в последнем запуске: {len(trend.latest_high_risk_modules)}",
    ]
    if trend.latest_high_risk_modules:
        lines.extend(["", "## Текущие high-risk модули", *[f"- {name}" for name in trend.latest_high_risk_modules]])
    return "\n".join(lines) + "\n"
