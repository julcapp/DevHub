from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable
from uuid import uuid4


class WorkflowRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class WorkflowContext:
    variables: dict[str, Any] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)


WorkflowHandler = Callable[[WorkflowContext], Any]


@dataclass(frozen=True, slots=True)
class WorkflowNode:
    node_id: str
    title: str
    handler: WorkflowHandler

    def __post_init__(self) -> None:
        normalized = self.node_id.strip().lower()
        if not normalized:
            raise ValueError("Workflow node_id cannot be empty")
        object.__setattr__(self, "node_id", normalized)


@dataclass(frozen=True, slots=True)
class Workflow:
    title: str
    nodes: tuple[WorkflowNode, ...]
    workflow_id: str = field(default_factory=lambda: f"WF-{uuid4().hex[:12].upper()}")
    version: int = 1
    tags: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Workflow title cannot be empty")
        if not self.nodes:
            raise ValueError("Workflow must contain at least one node")
        node_ids = [node.node_id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Workflow node_id values must be unique")


@dataclass(slots=True)
class WorkflowRun:
    workflow_id: str
    run_id: str = field(default_factory=lambda: f"WFR-{uuid4().hex[:12].upper()}")
    status: WorkflowRunStatus = WorkflowRunStatus.PENDING
    current_node_id: str | None = None
    error: str | None = None
