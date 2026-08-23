from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    label: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    relation: str
    attributes: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    """Минимальное in-memory ядро инженерного графа знаний."""

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []

    @property
    def nodes(self) -> tuple[Node, ...]:
        return tuple(self._nodes.values())

    @property
    def edges(self) -> tuple[Edge, ...]:
        return tuple(self._edges)

    def add_node(self, node: Node) -> None:
        self._nodes[node.id] = node

    def get_node(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    def add_edge(self, edge: Edge) -> None:
        if edge.source not in self._nodes or edge.target not in self._nodes:
            raise KeyError("Оба узла связи должны существовать в графе")
        if edge not in self._edges:
            self._edges.append(edge)

    def neighbors(self, node_id: str, relation: str | None = None) -> list[Node]:
        if node_id not in self._nodes:
            return []
        result: list[Node] = []
        seen: set[str] = set()
        for edge in self._edges:
            if relation is not None and edge.relation != relation:
                continue
            other_id: str | None = None
            if edge.source == node_id:
                other_id = edge.target
            elif edge.target == node_id:
                other_id = edge.source
            if other_id is not None and other_id not in seen:
                seen.add(other_id)
                result.append(self._nodes[other_id])
        return result

    def outgoing(self, node_id: str, relation: str | None = None) -> list[Edge]:
        return [
            edge
            for edge in self._edges
            if edge.source == node_id and (relation is None or edge.relation == relation)
        ]

    def remove_node(self, node_id: str) -> None:
        self._nodes.pop(node_id, None)
        self._edges = [
            edge for edge in self._edges if edge.source != node_id and edge.target != node_id
        ]

    def clear(self) -> None:
        self._nodes.clear()
        self._edges.clear()
