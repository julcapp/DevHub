from devhub.events import EventBus
from devhub.missions import (
    Mission,
    MissionContext,
    MissionExecutor,
    MissionFailurePolicy,
    MissionRunStatus,
    MissionStep,
)
from devhub.workflows import (
    Workflow,
    WorkflowExecutor,
    WorkflowNode,
    WorkflowRegistry,
)


def _registry_with_workflows() -> WorkflowRegistry:
    registry = WorkflowRegistry()
    registry.register(Workflow(
        title="Collect",
        workflow_id="WF-COLLECT",
        nodes=(WorkflowNode("collect", "Collect", lambda _: 5),),
    ))
    registry.register(Workflow(
        title="Report",
        workflow_id="WF-REPORT",
        nodes=(WorkflowNode("report", "Report", lambda ctx: ctx.variables["name"]),),
    ))
    registry.register(Workflow(
        title="Failure",
        workflow_id="WF-FAIL",
        nodes=(WorkflowNode("fail", "Fail", lambda _: (_ for _ in ()).throw(RuntimeError("boom"))),),
    ))
    return registry


def test_mission_executes_workflows_and_publishes_timeline() -> None:
    bus = EventBus()
    events = []
    bus.subscribe("*", events.append)
    registry = _registry_with_workflows()
    context = MissionContext(variables={"name": "daily-report"})
    mission = Mission(
        title="Daily audit",
        steps=(
            MissionStep("WF-COLLECT", "Collect data"),
            MissionStep("WF-REPORT", "Generate report"),
        ),
    )

    run = MissionExecutor(registry, WorkflowExecutor(bus), bus).execute(mission, context)

    assert run.status is MissionRunStatus.COMPLETED
    assert run.health_score == 100
    assert context.history == ["WF-COLLECT", "WF-REPORT"]
    assert context.workflow_results["WF-COLLECT"]["results"] == {"collect": 5}
    assert [event.name for event in events if event.name.startswith("mission.")] == [
        "mission.run.started",
        "mission.workflow.started",
        "mission.workflow.completed",
        "mission.workflow.started",
        "mission.workflow.completed",
        "mission.run.completed",
    ]


def test_mission_can_continue_after_noncritical_failure() -> None:
    registry = _registry_with_workflows()
    context = MissionContext(variables={"name": "continued"})
    mission = Mission(
        title="Resilient audit",
        steps=(
            MissionStep("WF-FAIL", "Optional check", MissionFailurePolicy.CONTINUE),
            MissionStep("WF-REPORT", "Generate report"),
        ),
    )

    run = MissionExecutor(registry, WorkflowExecutor()).execute(mission, context)

    assert run.status is MissionRunStatus.COMPLETED_WITH_WARNINGS
    assert run.health_score == 50
    assert context.errors == ["boom"]
    assert "WF-REPORT" in context.workflow_results


def test_mission_stops_on_critical_failure() -> None:
    registry = _registry_with_workflows()
    mission = Mission(
        title="Strict audit",
        steps=(
            MissionStep("WF-FAIL", "Critical check"),
            MissionStep("WF-REPORT", "Must not run"),
        ),
    )

    context = MissionContext(variables={"name": "unused"})
    run = MissionExecutor(registry, WorkflowExecutor()).execute(mission, context)

    assert run.status is MissionRunStatus.FAILED
    assert run.health_score == 50
    assert context.history == ["WF-FAIL"]
    assert "WF-REPORT" not in context.workflow_results
