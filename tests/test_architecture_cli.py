from pathlib import Path

from app.workspaces.architecture.baseline import ArchitectureBaselineStore
from app.workspaces.architecture.cli import run_quality_gate
from app.workspaces.architecture.controller import ArchitectureWorkspaceController


def test_cli_quality_gate_passes_without_baseline(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def hello():\n    return 'ok'\n", encoding="utf-8")
    code, payload = run_quality_gate(tmp_path)
    assert code == 0
    assert payload["quality_gate"] == "PASS"


def test_cli_quality_gate_fails_on_regression(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def a():\n    return 1\n", encoding="utf-8")
    summary = ArchitectureWorkspaceController().analyze(tmp_path)
    ArchitectureBaselineStore().save(tmp_path, summary)
    (tmp_path / "a.py").write_text("import b\ndef a():\n    return b.b()\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("import a\ndef b():\n    return a.a()\n", encoding="utf-8")
    code, payload = run_quality_gate(tmp_path)
    assert code == 2
    assert payload["quality_gate"] == "FAIL"
    assert payload["violations"]


def test_cli_quality_gate_compares_separate_base_checkout(tmp_path: Path) -> None:
    base = tmp_path / "base"
    current = tmp_path / "current"
    base.mkdir(); current.mkdir()
    (base / "a.py").write_text("def a():\n    return 1\n", encoding="utf-8")
    (current / "a.py").write_text("import b\ndef a():\n    return b.b()\n", encoding="utf-8")
    (current / "b.py").write_text("import a\ndef b():\n    return a.a()\n", encoding="utf-8")

    code, payload = run_quality_gate(current, base)

    assert code == 2
    assert payload["quality_gate"] == "FAIL"
    assert payload["baseline_source"] == str(base.resolve())
