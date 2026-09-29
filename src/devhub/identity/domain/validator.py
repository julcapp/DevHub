"""Pure validation functions for Identity Core domain values."""

import re

from devhub.identity.domain.exceptions import InvalidIdentityError

_IDENTITY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


def validate_identity_value(value: str) -> str:
    """Validate and return an identity value.

    Values are stable, lowercase, ASCII identifiers between 1 and 128
    characters. Dots, underscores, and hyphens are allowed after the first
    character.
    """

    if not isinstance(value, str):
        raise InvalidIdentityError("Identity value must be a string.")
    if not _IDENTITY_PATTERN.fullmatch(value):
        raise InvalidIdentityError(
            "Identity value must match ^[a-z0-9][a-z0-9._-]{0,127}$."
        )
    return value


def validate_strategy_name(value: str) -> str:
    """Validate and return a strategy name."""

    if not isinstance(value, str) or not _IDENTITY_PATTERN.fullmatch(value):
        raise InvalidIdentityError("Strategy name must be a valid identity token.")
    return value


def validate_version(value: int) -> int:
    """Validate and return a positive descriptor version."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InvalidIdentityError("Identity descriptor version must be positive.")
    return value
