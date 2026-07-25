from __future__ import annotations

from devhub.events import Event, EventBus
from devhub.workflows import WorkflowContext, WorkflowExecutor, WorkflowRegistry, WorkflowRunStatus

from .model import (
    Mission,
    MissionContext,
    MissionFailurePolicy,
    MissionRun,
    MissionRunStatus,
)


class MissionExecutor:
    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        workflow_executor: WorkflowExecutor,
        event_bus: EventBus | None = None,
    ) -> None:
        self._workflow_registry = workflow_registry
        self._workflow_executor = workflow_executor
        self._event_bus = event_bus

    def execute(self, mission: Mission, context: MissionContext | None = None) -> MissionRun:
        context = context or MissionContext()
        run = MissionRun(mission_id=mission.mission_id)
        run.start()
        self._publish("mission.run.started", mission, run)

        failed_steps = 0
        for step in mission.steps:
            run.current_workflow_id = step.workflow_id
            context.history.append(step.workflow_id)
            self._publish("mission.workflow.started", mission, run, workflow_id=step.workflow_id)

            try:
                workflow = self._workflow_registry.get(step.workflow_id)
                workflow_context = WorkflowContext(variables=dict(context.variables))
                workflow_run = self._workflow_executor.execute(workflow, workflow_context)
            except Exception as exc:
                failed_steps += 1
                message = f"{step.workflow_id}: {exc}"
                context.errors.append(message)
                self._publish("mission.workflow.failed", mission, run, workflow_id=step.workflow_id, error=message)
                if step.failure_policy is MissionFailurePolicy.STOP:
                    run.error = message
                    run.health_score = self._health_score(len(mission.steps), failed_steps)
                    run.finish(MissionRunStatus.FAILED)
                    self._publish("mission.run.failed", mission, run, error=message)
                    return run
                continue

            context.workflow_results[step.workflow_id] = {
                "run": workflow_run,
                "results": dict(workflow_context.results),
            }

            if workflow_run.status is WorkflowRunStatus.FAILED:
                failed_steps += 1
                message = workflow_run.error or f"Workflow failed: {step.workflow_id}"
                context.errors.append(message)
                self._publish("mission.workflow.failed", mission, run, workflow_id=step.workflow_id, error=message)
                if step.failure_policy is MissionFailurePolicy.STOP:
                    run.error = message
                    run.health_score = self._health_score(len(mission.steps), failed_steps)
                    run.finish(MissionRunStatus.FAILED)
                    self._publish("mission.run.failed", mission, run, error=message)
                    return run
            else:
                self._publish("mission.workflow.completed", mission, run, workflow_id=step.workflow_id)

        run.health_score = self._health_score(len(mission.steps), failed_steps)
        final_status = (
            MissionRunStatus.COMPLETED_WITH_WARNINGS
            if failed_steps
            else MissionRunStatus.COMPLETED
        )
        run.finish(final_status)
        self._publish("mission.run.completed", mission, run, health_score=run.health_score)
        return run

    @staticmethod
    def _health_score(total_steps: int, failed_steps: int) -> int:
        if total_steps <= 0:
            return 0
        return max(0, round(100 * (total_steps - failed_steps) / total_steps))

    def _publish(self, name: str, mission: Mission, run: MissionRun, **payload: object) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(Event(
            name=name,
            source="mission.executor",
            correlation_id=run.run_id,
            payload={"mission_id": mission.mission_id, "run_id": run.run_id, **payload},
        ))
