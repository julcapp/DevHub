"""Tests for module manifest parsing and filesystem discovery."""

from pathlib import Path

import pytest

from devhub.runtime.application import ManifestParser, ModuleDiscovery
from devhub.runtime.domain import DiscoveryError, ManifestError, ModuleManifest


VALID_MANIFEST = """\
id: devhub.example
name: Example Module
version: 1.2.3
api_version: 1
description: Example module for tests.
entrypoint: devhub.example.bootstrap:create_module
dependencies:
  - devhub.identity
  - devhub.config
"""


def test_parser_builds_immutable_manifest() -> None:
    manifest = ManifestParser().parse(VALID_MANIFEST)

    assert manifest == ModuleManifest(
        id="devhub.example",
        name="Example Module",
        version="1.2.3",
        api_version=1,
        description="Example module for tests.",
        entrypoint="devhub.example.bootstrap:create_module",
        dependencies=("devhub.identity", "devhub.config"),
    )


def test_parser_supports_empty_inline_dependencies() -> None:
    manifest = ManifestParser().parse(
        "id: devhub.example\nname: Example\nversion: 1.0.0\napi_version: 1\ndependencies: []\n"
    )

    assert manifest.dependencies == ()


@pytest.mark.parametrize(
    "text",
    [
        "name: Missing ID\nversion: 1.0.0\napi_version: 1\n",
        "id: invalid\nname: Invalid ID\nversion: 1.0.0\napi_version: 1\n",
        "id: devhub.example\nname: Example\nversion: latest\napi_version: 1\n",
        "id: devhub.example\nname: Example\nversion: 1.0.0\napi_version: zero\n",
        "id: devhub.example\nname: Example\nversion: 1.0.0\napi_version: 1\nunknown: value\n",
    ],
)
def test_parser_rejects_invalid_manifests(text: str) -> None:
    with pytest.raises(ManifestError):
        ManifestParser().parse(text)


def test_manifest_rejects_self_dependency() -> None:
    with pytest.raises(ManifestError):
        ManifestParser().parse(
            "id: devhub.example\nname: Example\nversion: 1.0.0\n"
            "api_version: 1\ndependencies:\n  - devhub.example\n"
        )


def test_discovery_finds_manifests_in_stable_order(tmp_path: Path) -> None:
    second = tmp_path / "second"
    first = tmp_path / "first"
    second.mkdir()
    first.mkdir()
    (second / "module.yaml").write_text(
        "id: devhub.second\nname: Second\nversion: 1.0.0\napi_version: 1\n",
        encoding="utf-8",
    )
    (first / "module.yaml").write_text(
        "id: devhub.first\nname: First\nversion: 1.0.0\napi_version: 1\n",
        encoding="utf-8",
    )

    manifests = ModuleDiscovery().discover((tmp_path,))

    assert [manifest.id for manifest in manifests] == ["devhub.first", "devhub.second"]
    assert all(manifest.path is not None for manifest in manifests)


def test_discovery_rejects_duplicate_module_ids(tmp_path: Path) -> None:
    for directory in (tmp_path / "one", tmp_path / "two"):
        directory.mkdir()
        (directory / "module.yaml").write_text(
            "id: devhub.duplicate\nname: Duplicate\nversion: 1.0.0\napi_version: 1\n",
            encoding="utf-8",
        )

    with pytest.raises(DiscoveryError, match="Duplicate module id"):
        ModuleDiscovery().discover((tmp_path,))


def test_discovery_wraps_invalid_manifest_error(tmp_path: Path) -> None:
    module = tmp_path / "broken"
    module.mkdir()
    (module / "module.yaml").write_text("id: broken\n", encoding="utf-8")

    with pytest.raises(DiscoveryError, match="Invalid manifest"):
        ModuleDiscovery().discover((tmp_path,))


def test_discovery_rejects_missing_root(tmp_path: Path) -> None:
    with pytest.raises(DiscoveryError, match="does not exist"):
        ModuleDiscovery().discover((tmp_path / "missing",))
