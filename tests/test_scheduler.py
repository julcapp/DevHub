from datetime import datetime, time, timedelta, timezone

from devhub.events import EventBus
from devhub.scheduler import DailySchedule, IntervalSchedule, RunStatus, ScheduledJob, Scheduler
from devhub.workflows import Workflow, WorkflowExecutor, WorkflowNode, WorkflowRegistry


def test_daily_schedule_runs_workflow_at_0800() -> None:
    bus = EventBus()
    events = []
    bus.subscribe("*", events.append)

    workflow = Workflow(
        title="Morning check",
        nodes=(WorkflowNode("check", "Check", lambda _: "ok"),),
    )
    registry = WorkflowRegistry()
    registry.register(workflow)
    scheduler = Scheduler(registry, WorkflowExecutor(bus), bus)

    before = datetime(2026, 7, 25, 7, 0, tzinfo=timezone.utc)
    job = ScheduledJob(
        title="Run at eight",
        workflow_id=workflow.workflow_id,
        schedule=DailySchedule(time(8, 0), "UTC"),
    )
    scheduler.register(job, before)

    assert scheduler.tick(datetime(2026, 7, 25, 7, 59, tzinfo=timezone.utc)) == ()
    runs = scheduler.tick(datetime(2026, 7, 25, 8, 0, tzinfo=timezone.utc))

    assert len(runs) == 1
    assert runs[0].status is RunStatus.COMPLETED
    assert job.next_run_at == datetime(2026, 7, 26, 8, 0, tzinfo=timezone.utc)
    assert "scheduler.run.completed" in [event.name for event in events]


def test_interval_job_can_be_paused_and_resumed() -> None:
    workflow = Workflow(title="Ping", nodes=(WorkflowNode("ping", "Ping", lambda _: True),))
    registry = WorkflowRegistry()
    registry.register(workflow)
    scheduler = Scheduler(registry, WorkflowExecutor())
    start = datetime(2026, 7, 25, 8, 0, tzinfo=timezone.utc)
    job = ScheduledJob(
        title="Every hour",
        workflow_id=workflow.workflow_id,
        schedule=IntervalSchedule(timedelta(hours=1)),
    )
    scheduler.register(job, start)
    scheduler.pause(job.job_id)

    assert scheduler.tick(start + timedelta(hours=1)) == ()

    scheduler.resume(job.job_id, start + timedelta(hours=1))
    runs = scheduler.tick(start + timedelta(hours=2))

    assert len(runs) == 1
    assert scheduler.list_runs(job.job_id) == runs
