"""Validated module manifest model."""

from dataclasses import dataclass
from pathlib import Path
import re

from devhub.runtime.domain.exceptions import ManifestError

_MODULE_ID = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9_-]*)+$")
_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
_ENTRYPOINT = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True, slots=True)
class ModuleManifest:
    """Immutable, validated description of one discoverable module."""

    id: str
    name: str
    version: str
    api_version: int
    dependencies: tuple[str, ...] = ()
    description: str = ""
    entrypoint: str | None = None
    path: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not _MODULE_ID.fullmatch(self.id):
            raise ManifestError(f"Invalid module id: {self.id!r}.")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ManifestError("Module name must not be empty.")
        if not isinstance(self.version, str) or not _VERSION.fullmatch(self.version):
            raise ManifestError(f"Invalid semantic version: {self.version!r}.")
        if (
            not isinstance(self.api_version, int)
            or isinstance(self.api_version, bool)
            or self.api_version < 1
        ):
            raise ManifestError("api_version must be a positive integer.")
        if not isinstance(self.dependencies, tuple) or not all(
            isinstance(item, str) for item in self.dependencies
        ):
            raise ManifestError("dependencies must be a tuple of module ids.")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ManifestError("Module dependencies must be unique.")
        if self.id in self.dependencies:
            raise ManifestError("A module cannot depend on itself.")
        for dependency in self.dependencies:
            if not _MODULE_ID.fullmatch(dependency):
                raise ManifestError(f"Invalid dependency id: {dependency!r}.")
        if self.entrypoint is not None and (
            not isinstance(self.entrypoint, str)
            or not _ENTRYPOINT.fullmatch(self.entrypoint)
        ):
            raise ManifestError(
                "entrypoint must use the 'package.module:Factory' format."
            )
        if self.path is not None and (
            not isinstance(self.path, Path) or self.path.name != "module.yaml"
        ):
            raise ManifestError("Manifest path must point to module.yaml.")
