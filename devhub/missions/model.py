from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class MissionRunStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MissionFailurePolicy(StrEnum):
    STOP = "stop"
    CONTINUE = "continue"


@dataclass(frozen=True, slots=True)
class MissionStep:
    workflow_id: str
    title: str
    failure_policy: MissionFailurePolicy = MissionFailurePolicy.STOP

    def __post_init__(self) -> None:
        if not self.workflow_id.strip():
            raise ValueError("Mission step workflow_id cannot be empty")
        if not self.title.strip():
            raise ValueError("Mission step title cannot be empty")


@dataclass(frozen=True, slots=True)
class Mission:
    title: str
    steps: tuple[MissionStep, ...]
    mission_id: str = field(default_factory=lambda: f"MSN-{uuid4().hex[:12].upper()}")
    version: int = 1
    tags: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Mission title cannot be empty")
        if not self.steps:
            raise ValueError("Mission must contain at least one step")


@dataclass(slots=True)
class MissionContext:
    variables: dict[str, Any] = field(default_factory=dict)
    workflow_results: dict[str, Any] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MissionRun:
    mission_id: str
    run_id: str = field(default_factory=lambda: f"MSR-{uuid4().hex[:12].upper()}")
    status: MissionRunStatus = MissionRunStatus.CREATED
    current_workflow_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    health_score: int = 100
    error: str | None = None

    def start(self) -> None:
        self.status = MissionRunStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def finish(self, status: MissionRunStatus) -> None:
        self.status = status
        self.current_workflow_id = None
        self.finished_at = datetime.now(timezone.utc)
