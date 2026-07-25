"""Import and API-boundary tests for Identity Core contracts."""

from pathlib import Path
import sys

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from devhub.identity import __all__ as public_api
from devhub.identity.contracts import (
    Clock,
    EventPublisher,
    IdentityProvider,
    IdentityRegistry,
    IdentityStrategy,
    MetricsCollector,
)


def test_contracts_are_importable() -> None:
    assert all(
        contract is not None
        for contract in (
            Clock,
            EventPublisher,
            IdentityProvider,
            IdentityRegistry,
            IdentityStrategy,
            MetricsCollector,
        )
    )


def test_public_api_is_empty_until_implemented() -> None:
    assert public_api == []
