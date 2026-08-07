import pytest

from app.knowledge import Edge, KnowledgeGraph, Node


def test_add_nodes_and_relation() -> None:
    graph = KnowledgeGraph()
    graph.add_node(Node("project:devhub", "Project", "DevHub"))
    graph.add_node(Node("file:main", "File", "main.py"))
    graph.add_edge(Edge("project:devhub", "file:main", "contains"))

    assert graph.get_node("file:main") is not None
    assert graph.outgoing("project:devhub", "contains")[0].target == "file:main"
    assert [node.id for node in graph.neighbors("project:devhub")] == ["file:main"]


def test_edge_requires_existing_nodes() -> None:
    graph = KnowledgeGraph()
    graph.add_node(Node("project:devhub", "Project", "DevHub"))

    with pytest.raises(KeyError):
        graph.add_edge(Edge("project:devhub", "file:missing", "contains"))


def test_remove_node_removes_related_edges() -> None:
    graph = KnowledgeGraph()
    graph.add_node(Node("a", "Project", "A"))
    graph.add_node(Node("b", "File", "B"))
    graph.add_edge(Edge("a", "b", "contains"))

    graph.remove_node("b")

    assert graph.get_node("b") is None
    assert graph.edges == ()
