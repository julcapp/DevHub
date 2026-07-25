from __future__ import annotations

from devhub.events import Event, EventBus

from .model import Workflow, WorkflowContext, WorkflowRun, WorkflowRunStatus


class WorkflowExecutor:
    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus

    def execute(self, workflow: Workflow, context: WorkflowContext | None = None) -> WorkflowRun:
        context = context or WorkflowContext()
        run = WorkflowRun(workflow_id=workflow.workflow_id, status=WorkflowRunStatus.RUNNING)
        self._publish("workflow.run.started", workflow, run)

        try:
            for node in workflow.nodes:
                run.current_node_id = node.node_id
                context.history.append(node.node_id)
                self._publish("workflow.node.started", workflow, run, node_id=node.node_id)
                result = node.handler(context)
                context.results[node.node_id] = result
                self._publish("workflow.node.completed", workflow, run, node_id=node.node_id)
        except Exception as exc:
            run.status = WorkflowRunStatus.FAILED
            run.error = str(exc)
            self._publish("workflow.run.failed", workflow, run, error=run.error)
            return run

        run.current_node_id = None
        run.status = WorkflowRunStatus.COMPLETED
        self._publish("workflow.run.completed", workflow, run)
        return run

    def _publish(self, name: str, workflow: Workflow, run: WorkflowRun, **payload: object) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(Event(
            name=name,
            source="workflow.executor",
            correlation_id=run.run_id,
            payload={"workflow_id": workflow.workflow_id, "run_id": run.run_id, **payload},
        ))
