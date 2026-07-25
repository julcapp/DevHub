"""Filesystem discovery of DevHub module manifests."""

from pathlib import Path

from devhub.runtime.application.manifest_parser import ManifestParser
from devhub.runtime.domain.exceptions import DiscoveryError, ManifestError
from devhub.runtime.domain.manifest import ModuleManifest


class ModuleDiscovery:
    """Discover and parse module.yaml files below configured roots."""

    def __init__(self, *, parser: ManifestParser | None = None) -> None:
        self._parser = parser or ManifestParser()

    def discover(self, roots: tuple[Path, ...]) -> tuple[ModuleManifest, ...]:
        """Return manifests sorted by module id with duplicate ids rejected."""

        manifests: dict[str, ModuleManifest] = {}
        for root in roots:
            if not root.exists():
                raise DiscoveryError(f"Discovery root does not exist: {root}.")
            if not root.is_dir():
                raise DiscoveryError(f"Discovery root is not a directory: {root}.")

            for path in sorted(root.rglob("module.yaml")):
                try:
                    manifest = self._parser.parse_file(path)
                except ManifestError as error:
                    raise DiscoveryError(f"Invalid manifest at {path}: {error}") from error
                previous = manifests.get(manifest.id)
                if previous is not None:
                    raise DiscoveryError(
                        f"Duplicate module id {manifest.id!r}: "
                        f"{previous.path} and {manifest.path}."
                    )
                manifests[manifest.id] = manifest

        return tuple(manifests[module_id] for module_id in sorted(manifests))
