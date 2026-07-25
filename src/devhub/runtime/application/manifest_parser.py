"""Strict parser for the supported module.yaml schema."""

from pathlib import Path
from typing import Any

from devhub.runtime.domain.exceptions import ManifestError
from devhub.runtime.domain.manifest import ModuleManifest

_REQUIRED = {"id", "name", "version", "api_version"}
_ALLOWED = _REQUIRED | {"description", "dependencies", "entrypoint"}


class ManifestParser:
    """Parse the small, deterministic YAML subset used by DevHub manifests."""

    def parse_file(self, path: Path) -> ModuleManifest:
        """Read and validate one module.yaml file."""

        if path.name != "module.yaml":
            raise ManifestError(f"Expected module.yaml, received {path.name!r}.")
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            raise ManifestError(f"Cannot read manifest {path}: {error}") from error
        return self.parse(text, path=path)

    def parse(self, text: str, *, path: Path | None = None) -> ModuleManifest:
        """Parse manifest text into an immutable domain object."""

        values = self._parse_mapping(text)
        unknown = set(values) - _ALLOWED
        if unknown:
            names = ", ".join(sorted(unknown))
            raise ManifestError(f"Unknown manifest fields: {names}.")
        missing = _REQUIRED - set(values)
        if missing:
            names = ", ".join(sorted(missing))
            raise ManifestError(f"Missing required manifest fields: {names}.")

        dependencies = values.get("dependencies", [])
        if not isinstance(dependencies, list) or not all(
            isinstance(item, str) for item in dependencies
        ):
            raise ManifestError("dependencies must be a list of module ids.")

        api_version = values["api_version"]
        if not isinstance(api_version, int) or isinstance(api_version, bool):
            raise ManifestError("api_version must be an integer.")

        return ModuleManifest(
            id=self._require_string(values, "id"),
            name=self._require_string(values, "name"),
            version=self._require_string(values, "version"),
            api_version=api_version,
            description=self._optional_string(values, "description"),
            dependencies=tuple(dependencies),
            entrypoint=self._optional_nullable_string(values, "entrypoint"),
            path=path,
        )

    @staticmethod
    def _require_string(values: dict[str, Any], key: str) -> str:
        value = values[key]
        if not isinstance(value, str):
            raise ManifestError(f"{key} must be a string.")
        return value

    @staticmethod
    def _optional_string(values: dict[str, Any], key: str) -> str:
        value = values.get(key, "")
        if not isinstance(value, str):
            raise ManifestError(f"{key} must be a string.")
        return value

    @staticmethod
    def _optional_nullable_string(values: dict[str, Any], key: str) -> str | None:
        value = values.get(key)
        if value is not None and not isinstance(value, str):
            raise ManifestError(f"{key} must be a string or null.")
        return value

    @staticmethod
    def _parse_mapping(text: str) -> dict[str, Any]:
        values: dict[str, Any] = {}
        active_list: str | None = None

        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if stripped.startswith("-"):
                if active_list is None:
                    raise ManifestError(f"Unexpected list item on line {line_number}.")
                item = stripped[1:].strip()
                if not item:
                    raise ManifestError(f"Empty list item on line {line_number}.")
                cast_list = values[active_list]
                assert isinstance(cast_list, list)
                cast_list.append(ManifestParser._parse_scalar(item))
                continue

            if ":" not in stripped:
                raise ManifestError(f"Expected 'key: value' on line {line_number}.")
            key, raw_value = stripped.split(":", 1)
            key = key.strip()
            if not key or key in values:
                raise ManifestError(f"Invalid or duplicate key on line {line_number}.")

            raw_value = raw_value.strip()
            if not raw_value:
                values[key] = []
                active_list = key
            else:
                values[key] = ManifestParser._parse_scalar(raw_value)
                active_list = None

        return values

    @staticmethod
    def _parse_scalar(raw: str) -> Any:
        if raw == "[]":
            return []
        if raw in {"null", "~"}:
            return None
        if raw.isdecimal():
            return int(raw)
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
            return raw[1:-1]
        return raw
