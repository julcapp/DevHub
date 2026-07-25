from __future__ import annotations

from .model import Workflow


class WorkflowRegistry:
    def __init__(self) -> None:
        self._workflows: dict[str, Workflow] = {}

    def register(self, workflow: Workflow) -> None:
        if workflow.workflow_id in self._workflows:
            raise ValueError(f"Workflow already registered: {workflow.workflow_id}")
        self._workflows[workflow.workflow_id] = workflow

    def get(self, workflow_id: str) -> Workflow:
        try:
            return self._workflows[workflow_id]
        except KeyError as exc:
            raise KeyError(f"Unknown workflow: {workflow_id}") from exc

    def list(self) -> tuple[Workflow, ...]:
        return tuple(self._workflows.values())
