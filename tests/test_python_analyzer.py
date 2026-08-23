from pathlib import Path

from app.indexer.analyzers import PythonAnalyzer


def test_python_analyzer_extracts_symbols_and_imports(tmp_path: Path) -> None:
    package = tmp_path / "app"
    package.mkdir()
    source = package / "service.py"
    source.write_text(
        "import json\n"
        "from pathlib import Path\n\n"
        "class Service:\n"
        "    def run(self):\n"
        "        return Path('.')\n\n"
        "async def load():\n"
        "    return json.loads('{}')\n",
        encoding="utf-8",
    )

    analysis = PythonAnalyzer().analyze(source, tmp_path)

    assert analysis.module == "app.service"
    assert {symbol.kind for symbol in analysis.symbols} == {"Class", "Method", "Function"}
    assert {symbol.qualified_name for symbol in analysis.symbols} == {
        "app.service.Service",
        "app.service.Service.run",
        "app.service.load",
    }
    assert analysis.imports == ("json", "pathlib")


def test_python_analyzer_preserves_relative_import_target(tmp_path: Path) -> None:
    package = tmp_path / "app" / "services"
    package.mkdir(parents=True)
    source = package / "worker.py"
    source.write_text("from .. import models\nfrom .helpers import run\n", encoding="utf-8")

    analysis = PythonAnalyzer().analyze(source, tmp_path)

    assert analysis.module == "app.services.worker"
    assert analysis.imports == ("..models", ".helpers")


def test_python_analyzer_rejects_invalid_syntax(tmp_path: Path) -> None:
    source = tmp_path / "broken.py"
    source.write_text("def broken(:\n", encoding="utf-8")

    try:
        PythonAnalyzer().analyze(source, tmp_path)
    except ValueError as error:
        assert "Ошибка синтаксиса Python" in str(error)
    else:
        raise AssertionError("ValueError expected")
