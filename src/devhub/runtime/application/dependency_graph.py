"""Dependency graph construction from validated manifests."""

from collections.abc import Sequence

from devhub.runtime.domain.dependency import DependencyGraph
from devhub.runtime.domain.exceptions import DependencyError
from devhub.runtime.domain.manifest import ModuleManifest


class DependencyGraphBuilder:
    """Build an immutable graph and reject unresolved dependencies."""

    def build(self, manifests: Sequence[ModuleManifest]) -> DependencyGraph:
        """Create a dependency graph from discovered manifests."""

        by_id = {manifest.id: manifest for manifest in manifests}
        if len(by_id) != len(manifests):
            raise DependencyError("Module manifests must have unique ids.")

        unknown: list[tuple[str, str]] = []
        for manifest in manifests:
            for dependency in manifest.dependencies:
                if dependency not in by_id:
                    unknown.append((manifest.id, dependency))

        if unknown:
            details = ", ".join(
                f"{module_id!r} -> {dependency!r}"
                for module_id, dependency in sorted(unknown)
            )
            raise DependencyError(f"Unknown module dependencies: {details}.")

        return DependencyGraph(
            {
                manifest.id: tuple(manifest.dependencies)
                for manifest in sorted(manifests, key=lambda item: item.id)
            }
        )
