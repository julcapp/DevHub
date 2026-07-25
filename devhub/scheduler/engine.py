from __future__ import annotations

from datetime import datetime, timezone

from devhub.events import Event, EventBus
from devhub.workflows import WorkflowExecutor, WorkflowRegistry, WorkflowRunStatus

from .model import JobRun, JobStatus, RunStatus, ScheduledJob


class Scheduler:
    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        workflow_executor: WorkflowExecutor,
        event_bus: EventBus | None = None,
    ) -> None:
        self._registry = workflow_registry
        self._executor = workflow_executor
        self._event_bus = event_bus
        self._jobs: dict[str, ScheduledJob] = {}
        self._runs: list[JobRun] = []

    def register(self, job: ScheduledJob, now: datetime | None = None) -> None:
        if job.job_id in self._jobs:
            raise ValueError(f"Job already registered: {job.job_id}")
        moment = now or datetime.now(timezone.utc)
        job.next_run_at = job.schedule.next_after(moment)
        self._jobs[job.job_id] = job
        self._publish("scheduler.job.created", job)

    def pause(self, job_id: str) -> None:
        job = self.get(job_id)
        job.enabled = False
        job.status = JobStatus.PAUSED
        self._publish("scheduler.job.paused", job)

    def resume(self, job_id: str, now: datetime | None = None) -> None:
        job = self.get(job_id)
        job.enabled = True
        job.status = JobStatus.SCHEDULED
        job.next_run_at = job.schedule.next_after(now or datetime.now(timezone.utc))
        self._publish("scheduler.job.resumed", job)

    def get(self, job_id: str) -> ScheduledJob:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise KeyError(f"Unknown job: {job_id}") from exc

    def list_jobs(self) -> tuple[ScheduledJob, ...]:
        return tuple(self._jobs.values())

    def list_runs(self, job_id: str | None = None) -> tuple[JobRun, ...]:
        return tuple(run for run in self._runs if job_id is None or run.job_id == job_id)

    def tick(self, now: datetime | None = None) -> tuple[JobRun, ...]:
        moment = now or datetime.now(timezone.utc)
        completed: list[JobRun] = []
        for job in self._jobs.values():
            if not job.enabled or job.next_run_at is None or job.next_run_at > moment:
                continue
            completed.append(self._run_job(job, moment))
        return tuple(completed)

    def _run_job(self, job: ScheduledJob, moment: datetime) -> JobRun:
        job.status = JobStatus.RUNNING
        job.last_run_at = moment
        run = JobRun(job_id=job.job_id, started_at=moment)
        self._runs.append(run)
        self._publish("scheduler.run.started", job, run_id=run.run_id)

        workflow = self._registry.get(job.workflow_id)
        workflow_run = self._executor.execute(workflow)
        run.workflow_run_id = workflow_run.run_id
        run.finished_at = moment

        if workflow_run.status is WorkflowRunStatus.COMPLETED:
            run.status = RunStatus.COMPLETED
            job.status = JobStatus.COMPLETED
            self._publish("scheduler.run.completed", job, run_id=run.run_id)
        else:
            run.status = RunStatus.FAILED
            run.error = workflow_run.error
            job.status = JobStatus.FAILED
            self._publish("scheduler.run.failed", job, run_id=run.run_id, error=run.error)

        job.last_status = run.status
        job.next_run_at = job.schedule.next_after(moment)
        if job.next_run_at is not None and job.enabled:
            job.status = JobStatus.SCHEDULED
        return run

    def _publish(self, name: str, job: ScheduledJob, **payload: object) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(Event(
            name=name,
            source="scheduler",
            correlation_id=job.job_id,
            payload={"job_id": job.job_id, "workflow_id": job.workflow_id, **payload},
        ))
