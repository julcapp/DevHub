from pathlib import Path

from app.indexer import ProjectIndexer


def test_project_indexer_builds_project_folder_file_graph(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")

    graph, result = ProjectIndexer().build_graph(tmp_path)

    assert result.files_indexed == 2
    assert result.folders_indexed == 1
    assert graph.get_node(result.project_id) is not None
    assert graph.get_node("folder:app") is not None
    assert graph.get_node("file:app/main.py") is not None
    assert graph.get_node("file:README.md") is not None
    assert {edge.target for edge in graph.outgoing(result.project_id, "contains")} == {
        "folder:app",
        "file:README.md",
    }


def test_project_indexer_ignores_service_directories(tmp_path: Path) -> None:
    ignored = tmp_path / ".git"
    ignored.mkdir()
    (ignored / "config").write_text("secret", encoding="utf-8")
    (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

    graph, result = ProjectIndexer().build_graph(tmp_path)

    assert result.files_indexed == 1
    assert graph.get_node("file:main.py") is not None
    assert all(".git" not in node.id for node in graph.nodes)


def test_project_indexer_adds_python_symbols_and_imports(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    source = app_dir / "service.py"
    source.write_text(
        "import json\n\n"
        "class Service:\n"
        "    def run(self):\n"
        "        return json.dumps({})\n",
        encoding="utf-8",
    )

    graph, result = ProjectIndexer().build_graph(tmp_path)

    assert result.python_files_analyzed == 1
    assert result.symbols_indexed == 2
    assert result.imports_indexed == 1
    assert result.internal_dependencies_resolved == 0
    assert graph.get_node("module:app.service") is not None
    assert graph.get_node("symbol:app.service.Service") is not None
    assert graph.get_node("symbol:app.service.Service.run") is not None
    assert graph.get_node("module-ref:json") is not None
    assert graph.outgoing("module:app.service", "imports")[0].target == "module-ref:json"


def test_project_indexer_resolves_absolute_internal_dependency(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "models.py").write_text("class Model:\n    pass\n", encoding="utf-8")
    (app_dir / "service.py").write_text(
        "import app.models\n\n"
        "def build():\n"
        "    return app.models.Model()\n",
        encoding="utf-8",
    )

    graph, result = ProjectIndexer().build_graph(tmp_path)

    dependencies = graph.outgoing("module:app.service", "depends_on")
    assert result.internal_dependencies_resolved == 1
    assert len(dependencies) == 1
    assert dependencies[0].target == "module:app.models"
    assert dependencies[0].attributes["import"] == "app.models"


def test_project_indexer_resolves_relative_internal_dependency(tmp_path: Path) -> None:
    package = tmp_path / "app" / "services"
    package.mkdir(parents=True)
    (tmp_path / "app" / "models.py").write_text("class Model:\n    pass\n", encoding="utf-8")
    (package / "worker.py").write_text(
        "from .. import models\n\n"
        "def run():\n"
        "    return models.Model()\n",
        encoding="utf-8",
    )

    graph, result = ProjectIndexer().build_graph(tmp_path)

    dependencies = graph.outgoing("module:app.services.worker", "depends_on")
    assert result.internal_dependencies_resolved == 1
    assert len(dependencies) == 1
    assert dependencies[0].target == "module:app"


def test_project_indexer_rejects_missing_root(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    try:
        ProjectIndexer().build_graph(missing)
    except FileNotFoundError as error:
        assert error.args[0] == missing.resolve()
    else:
        raise AssertionError("FileNotFoundError expected")
