"""Architecture fitness functions for Identity Core."""

from pathlib import Path


FORBIDDEN_DOMAIN_IMPORTS = (
    "devhub.identity.application",
    "devhub.identity.infrastructure",
)


def test_domain_does_not_depend_on_outer_layers() -> None:
    domain_root = Path(__file__).resolve().parents[2] / "src" / "devhub" / "identity" / "domain"
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in domain_root.rglob("*.py")
    )

    for forbidden_import in FORBIDDEN_DOMAIN_IMPORTS:
        assert forbidden_import not in source
