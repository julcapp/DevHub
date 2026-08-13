from __future__ import annotations

from dataclasses import dataclass

from app.workspaces.architecture.controller import ArchitectureSummary
from app.workspaces.architecture.quality_gate import QualityGateResult


@dataclass(frozen=True)
class ArchitectureReport:
    markdown: str
    health_delta: int | None
    added_cycles: tuple[str, ...]
    removed_cycles: tuple[str, ...]
    new_high_risk_modules: tuple[str, ...]
    resolved_high_risk_modules: tuple[str, ...]
    coupling_changes: tuple[str, ...]


def build_report(current: ArchitectureSummary, baseline: ArchitectureSummary | None, gate: QualityGateResult) -> ArchitectureReport:
    if baseline is None:
        markdown = (
            "# DevHub Architecture Quality Gate\n\n"
            f"**Status:** {'PASS' if gate.passed else 'FAIL'}\n\n"
            f"**Health:** {current.health_level} ({current.health_score}/100)\n\n"
            "Baseline is not available yet. This run establishes the architecture control bootstrap.\n"
        )
        return ArchitectureReport(markdown, None, (), (), (), (), ())

    health_delta = current.health_score - baseline.health_score
    baseline_cycles = {tuple(cycle) for cycle in baseline.cycles}
    current_cycles = {tuple(cycle) for cycle in current.cycles}
    added_cycles = tuple(sorted(" → ".join((*cycle, cycle[0])) for cycle in current_cycles - baseline_cycles))
    removed_cycles = tuple(sorted(" → ".join((*cycle, cycle[0])) for cycle in baseline_cycles - current_cycles))

    baseline_high = {item.name for item in baseline.module_details if item.risk_level == "Высокий"}
    current_high = {item.name for item in current.module_details if item.risk_level == "Высокий"}
    new_high = tuple(sorted(current_high - baseline_high))
    resolved_high = tuple(sorted(baseline_high - current_high))

    baseline_coupling = {item.name: item.coupling for item in baseline.module_details}
    current_coupling = {item.name: item.coupling for item in current.module_details}
    coupling_changes: list[str] = []
    for name in sorted(set(baseline_coupling) & set(current_coupling)):
        delta = current_coupling[name] - baseline_coupling[name]
        if delta:
            coupling_changes.append(f"{name}: {baseline_coupling[name]} → {current_coupling[name]} ({delta:+d})")

    lines = [
        "# DevHub Architecture Quality Gate",
        "",
        f"**Status:** {'PASS' if gate.passed else 'FAIL'}",
        f"**Health:** {baseline.health_score}/100 → {current.health_score}/100 ({health_delta:+d})",
        f"**Current level:** {current.health_level}",
        "",
    ]
    if gate.violations:
        lines.extend(["## Violations", *[f"- {item}" for item in gate.violations], ""])
    lines.extend(["## Architecture changes"])
    lines.append(f"- New cycles: {len(added_cycles)}")
    lines.append(f"- Resolved cycles: {len(removed_cycles)}")
    lines.append(f"- New high-risk modules: {len(new_high)}")
    lines.append(f"- Resolved high-risk modules: {len(resolved_high)}")
    lines.append("")
    if added_cycles:
        lines.extend(["### New cycles", *[f"- {item}" for item in added_cycles], ""])
    if removed_cycles:
        lines.extend(["### Resolved cycles", *[f"- {item}" for item in removed_cycles], ""])
    if new_high:
        lines.extend(["### New high-risk modules", *[f"- {item}" for item in new_high], ""])
    if resolved_high:
        lines.extend(["### Resolved high-risk modules", *[f"- {item}" for item in resolved_high], ""])
    if coupling_changes:
        lines.extend(["### Coupling changes", *[f"- {item}" for item in coupling_changes], ""])

    recommendations: list[str] = []
    by_name = {item.name: item for item in current.module_details}
    for name in new_high:
        module = by_name.get(name)
        if module:
            recommendations.extend(f"{name}: {text}" for text in module.recommendations)
    if recommendations:
        lines.extend(["## Recommended actions", *[f"- {item}" for item in dict.fromkeys(recommendations)], ""])

    return ArchitectureReport(
        "\n".join(lines).rstrip() + "\n",
        health_delta,
        added_cycles,
        removed_cycles,
        new_high,
        resolved_high,
        tuple(coupling_changes),
    )
