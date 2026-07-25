from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import StrEnum
from uuid import uuid4
from zoneinfo import ZoneInfo


class JobStatus(StrEnum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Schedule:
    def next_after(self, moment: datetime) -> datetime | None:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class OneTimeSchedule(Schedule):
    run_at: datetime

    def next_after(self, moment: datetime) -> datetime | None:
        return self.run_at if self.run_at > moment else None


@dataclass(frozen=True, slots=True)
class IntervalSchedule(Schedule):
    every: timedelta

    def __post_init__(self) -> None:
        if self.every <= timedelta(0):
            raise ValueError("Interval must be positive")

    def next_after(self, moment: datetime) -> datetime:
        return moment + self.every


@dataclass(frozen=True, slots=True)
class DailySchedule(Schedule):
    at: time
    timezone: str = "UTC"

    def next_after(self, moment: datetime) -> datetime:
        zone = ZoneInfo(self.timezone)
        local = moment.astimezone(zone)
        candidate = datetime.combine(local.date(), self.at, tzinfo=zone)
        if candidate <= local:
            candidate += timedelta(days=1)
        return candidate.astimezone(moment.tzinfo or ZoneInfo("UTC"))


@dataclass(slots=True)
class ScheduledJob:
    title: str
    workflow_id: str
    schedule: Schedule
    job_id: str = field(default_factory=lambda: f"JOB-{uuid4().hex[:12].upper()}")
    enabled: bool = True
    status: JobStatus = JobStatus.SCHEDULED
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    last_status: RunStatus | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Job title cannot be empty")
        if not self.workflow_id.strip():
            raise ValueError("workflow_id cannot be empty")


@dataclass(slots=True)
class JobRun:
    job_id: str
    workflow_run_id: str | None = None
    run_id: str = field(default_factory=lambda: f"JR-{uuid4().hex[:12].upper()}")
    status: RunStatus = RunStatus.RUNNING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
