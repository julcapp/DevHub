from pathlib import Path

from app.workspaces.architecture.controller import ArchitectureWorkspaceController


def test_top_risks_rank_highest_risk_first(tmp_path: Path) -> None:
    package = tmp_path / "app"
    package.mkdir()
    for name in "bcdefg":
        (package / f"{name}.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "a.py").write_text(
        "import app.b\nimport app.c\nimport app.d\nimport app.e\nimport app.f\nimport app.g\n"
        "class Service:\n"
        "    def run(self):\n"
        "        return 1\n",
        encoding="utf-8",
    )

    summary = ArchitectureWorkspaceController().analyze(tmp_path)

    assert summary.top_risks
    assert summary.top_risks[0].name == "app.a"
    assert summary.top_risks[0].risk_level == "Высокий"
    assert len(summary.top_risks) <= 5
    assert list(summary.top_risks) == sorted(
        summary.top_risks,
        key=lambda item: (-item.risk_score, -item.coupling, item.name),
    )
