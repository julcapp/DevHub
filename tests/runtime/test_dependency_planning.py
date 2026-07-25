"""Dependency graph, resolver, and execution planner tests."""

import pytest

from devhub.runtime.application import (
    DependencyGraphBuilder,
    DependencyResolver,
    ExecutionPlanner,
)
from devhub.runtime.domain import CircularDependencyError, DependencyError, ModuleManifest


def manifest(module_id: str, *dependencies: str) -> ModuleManifest:
    """Create a compact valid manifest for dependency tests."""

    return ModuleManifest(
        id=module_id,
        name=module_id,
        version="1.0.0",
        api_version=1,
        dependencies=dependencies,
    )


def test_graph_exposes_dependencies_dependents_roots_and_leaves() -> None:
    graph = DependencyGraphBuilder().build(
        (
            manifest("devhub.github", "devhub.config", "devhub.identity"),
            manifest("devhub.identity"),
            manifest("devhub.config"),
        )
    )

    assert graph.nodes == ("devhub.config", "devhub.github", "devhub.identity")
    assert graph.dependencies("devhub.github") == (
        "devhub.config",
        "devhub.identity",
    )
    assert graph.dependents("devhub.config") == ("devhub.github",)
    assert graph.roots == ("devhub.config", "devhub.identity")
    assert graph.leaves == ("devhub.github",)


def test_builder_rejects_unknown_dependencies() -> None:
    with pytest.raises(DependencyError, match="devhub.missing"):
        DependencyGraphBuilder().build(
            (manifest("devhub.github", "devhub.missing"),)
        )


def test_resolver_returns_dependency_first_stable_order() -> None:
    graph = DependencyGraphBuilder().build(
        (
            manifest("devhub.ai", "devhub.events", "devhub.github"),
            manifest("devhub.github", "devhub.identity"),
            manifest("devhub.events", "devhub.config"),
            manifest("devhub.identity"),
            manifest("devhub.config"),
        )
    )

    assert DependencyResolver().resolve(graph) == (
        "devhub.config",
        "devhub.events",
        "devhub.identity",
        "devhub.github",
        "devhub.ai",
    )


def test_resolver_reports_complete_cycle_path() -> None:
    graph = DependencyGraphBuilder().build(
        (
            manifest("devhub.alpha", "devhub.beta"),
            manifest("devhub.beta", "devhub.gamma"),
            manifest("devhub.gamma", "devhub.alpha"),
        )
    )

    with pytest.raises(
        CircularDependencyError,
        match=r"devhub\.alpha -> devhub\.beta -> devhub\.gamma -> devhub\.alpha",
    ):
        DependencyResolver().resolve(graph)


def test_planner_groups_independent_modules_into_levels() -> None:
    graph = DependencyGraphBuilder().build(
        (
            manifest("devhub.ai", "devhub.events", "devhub.github"),
            manifest("devhub.github", "devhub.identity"),
            manifest("devhub.events", "devhub.config"),
            manifest("devhub.identity"),
            manifest("devhub.config"),
        )
    )

    plan = ExecutionPlanner().plan(graph)

    assert plan.modules == (
        "devhub.config",
        "devhub.identity",
        "devhub.events",
        "devhub.github",
        "devhub.ai",
    )
    assert tuple(level.modules for level in plan.levels) == (
        ("devhub.config", "devhub.identity"),
        ("devhub.events", "devhub.github"),
        ("devhub.ai",),
    )


def test_planning_is_reproducible_for_different_manifest_order() -> None:
    manifests = (
        manifest("devhub.github", "devhub.identity"),
        manifest("devhub.identity"),
        manifest("devhub.config"),
    )

    first = ExecutionPlanner().plan(DependencyGraphBuilder().build(manifests))
    second = ExecutionPlanner().plan(DependencyGraphBuilder().build(tuple(reversed(manifests))))

    assert first == second
