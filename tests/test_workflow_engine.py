import pytest

from devhub.events import EventBus
from devhub.workflows import (
    Workflow,
    WorkflowContext,
    WorkflowExecutor,
    WorkflowNode,
    WorkflowRegistry,
    WorkflowRunStatus,
)


def test_workflow_executes_nodes_in_order_and_shares_context() -> None:
    context = WorkflowContext(variables={"value": 2})

    def double(ctx: WorkflowContext) -> int:
        return ctx.variables["value"] * 2

    def add_previous(ctx: WorkflowContext) -> int:
        return ctx.results["double"] + 3

    workflow = Workflow(
        title="Example",
        nodes=(
            WorkflowNode("double", "Double", double),
            WorkflowNode("add", "Add", add_previous),
        ),
    )

    run = WorkflowExecutor().execute(workflow, context)

    assert run.status is WorkflowRunStatus.COMPLETED
    assert context.history == ["double", "add"]
    assert context.results == {"double": 4, "add": 7}


def test_workflow_stops_on_failure_and_publishes_events() -> None:
    bus = EventBus()
    events = []
    bus.subscribe("*", events.append)

    def fail(_: WorkflowContext) -> None:
        raise RuntimeError("boom")

    workflow = Workflow(title="Failure", nodes=(WorkflowNode("fail", "Fail", fail),))
    run = WorkflowExecutor(bus).execute(workflow)

    assert run.status is WorkflowRunStatus.FAILED
    assert run.error == "boom"
    assert [event.name for event in events] == [
        "workflow.run.started",
        "workflow.node.started",
        "workflow.run.failed",
    ]


def test_registry_rejects_duplicate_workflow() -> None:
    workflow = Workflow(title="One", nodes=(WorkflowNode("step", "Step", lambda _: None),))
    registry = WorkflowRegistry()
    registry.register(workflow)

    with pytest.raises(ValueError):
        registry.register(workflow)
