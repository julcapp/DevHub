"""Domain exceptions raised by Identity Core."""


class IdentityError(Exception):
    """Base class for all Identity Core errors."""


class InvalidIdentityError(IdentityError):
    """Raised when an identity value violates domain rules."""


class IdentityCollisionError(IdentityError):
    """Raised when a generated identity already exists."""


class IdentityNotFoundError(IdentityError):
    """Raised when an identity descriptor cannot be resolved."""


class ParseIdentityError(IdentityError):
    """Raised when a serialized identity cannot be parsed."""


class UnknownStrategyError(IdentityError):
    """Raised when a requested identity strategy is not registered."""


class UnknownProviderError(IdentityError):
    """Raised when a requested identity provider is not registered."""


class InvalidEntityTypeError(IdentityError):
    """Raised when an entity type is not supported."""
