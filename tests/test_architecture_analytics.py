import json
from pathlib import Path

from app.workspaces.architecture.analytics import build_markdown, load_records, summarize


def test_architecture_analytics_builds_trend(tmp_path: Path) -> None:
    first = {
        "schema_version": 1,
        "project": "demo",
        "health_score": 70,
        "health_level": "Требует внимания",
        "quality_gate": "PASS",
        "cycles": 1,
        "high_risk_modules": ["app.a"],
        "run_id": "10",
    }
    second = {
        "schema_version": 1,
        "project": "demo",
        "health_score": 82,
        "health_level": "Хорошее",
        "quality_gate": "PASS",
        "cycles": 0,
        "high_risk_modules": [],
        "run_id": "11",
    }
    (tmp_path / "001.json").write_text(json.dumps(first, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "002.json").write_text(json.dumps(second, ensure_ascii=False), encoding="utf-8")

    records = load_records(tmp_path)
    trend = summarize(records)
    markdown = build_markdown(trend)

    assert trend.runs == 2
    assert trend.health_delta == 12
    assert trend.pass_count == 2
    assert trend.latest_high_risk_modules == ()
    assert "70/100 → 82/100 (+12)" in markdown


def test_architecture_analytics_ignores_unrelated_json(tmp_path: Path) -> None:
    (tmp_path / "unrelated.json").write_text('{"hello": "world"}', encoding="utf-8")
    records = load_records(tmp_path)
    trend = summarize(records)
    assert records == ()
    assert trend.runs == 0
