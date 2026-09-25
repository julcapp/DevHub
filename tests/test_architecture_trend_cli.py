import json
from pathlib import Path

from app.workspaces.architecture.trend_cli import main


def test_trend_cli_writes_markdown(tmp_path: Path, capsys) -> None:
    (tmp_path / "001.json").write_text(json.dumps({"schema_version": 1, "project": "demo", "health_score": 70, "health_level": "Требует внимания", "quality_gate": "PASS", "cycles": 1, "high_risk_modules": ["app.a"]}), encoding="utf-8")
    (tmp_path / "002.json").write_text(json.dumps({"schema_version": 1, "project": "demo", "health_score": 82, "health_level": "Хорошее", "quality_gate": "PASS", "cycles": 0, "high_risk_modules": []}), encoding="utf-8")
    output = tmp_path / "trend.md"
    assert main([str(tmp_path), "--json", "--markdown-output", str(output)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["runs"] == 2
    assert payload["health_delta"] == 12
    text = output.read_text(encoding="utf-8")
    assert "70/100 → 82/100 (+12)" in text
    assert "PASS: 2" in text


def test_trend_cli_handles_empty_directory(tmp_path: Path, capsys) -> None:
    assert main([str(tmp_path)]) == 0
    assert "Данные Quality Gate пока отсутствуют" in capsys.readouterr().out
