from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class ResourceURI:
    """Canonical address of a resource inside DevHub."""

    scheme: str
    authority: str
    path: str

    @classmethod
    def parse(cls, value: str) -> "ResourceURI":
        normalized = value.strip()
        if not normalized:
            raise ValueError("Resource URI cannot be empty")

        parsed = urlparse(normalized)
        if not parsed.scheme:
            raise ValueError(f"Resource URI has no scheme: {value!r}")

        path = parsed.path.lstrip("/")
        if not parsed.netloc and not path:
            raise ValueError(f"Resource URI has no target: {value!r}")

        return cls(
            scheme=parsed.scheme.lower(),
            authority=parsed.netloc,
            path=path,
        )

    def __str__(self) -> str:
        if self.authority:
            suffix = f"/{self.path}" if self.path else ""
            return f"{self.scheme}://{self.authority}{suffix}"
        return f"{self.scheme}:///{self.path}"
