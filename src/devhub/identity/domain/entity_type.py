"""Supported entity types for DevHub identities."""

from enum import StrEnum, auto


class EntityType(StrEnum):
    """Stable vocabulary of platform entity types."""

    MODULE = auto()
    WORKSPACE = auto()
    RESOURCE = auto()
    EVENT = auto()
    DOCUMENT = auto()
    SESSION = auto()
