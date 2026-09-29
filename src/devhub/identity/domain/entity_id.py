"""Immutable identity value object."""

from dataclasses import dataclass

from devhub.identity.domain.exceptions import InvalidIdentityError, ParseIdentityError
from devhub.identity.domain.validator import validate_identity_value


@dataclass(frozen=True, slots=True)
class EntityId:
    """Immutable, hashable identifier for a DevHub entity."""

    value: str

    def __post_init__(self) -> None:
        validate_identity_value(self.value)

    def __str__(self) -> str:
        return self.value

    def serialize(self) -> str:
        """Serialize the identifier to its stable string representation."""

        return self.value

    @classmethod
    def parse(cls, raw: str) -> "EntityId":
        """Parse an identifier and expose a parse-specific domain error."""

        try:
            return cls(raw)
        except InvalidIdentityError as error:
            raise ParseIdentityError(str(error)) from error
