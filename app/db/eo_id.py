from __future__ import annotations

PREFIXES = {
    "PROJECT": "PROJ",
    "REPOSITORY": "REPO",
    "STAR": "STAR",
    "IDEA": "IDEA",
    "RESEARCH": "RES",
    "TECHNOLOGY": "TECH",
    "ARTIFACT": "ART",
    "EVOLUTION": "EVO",
    "ADR": "ADR",
    "DOCUMENT": "DOC",
}


def format_eo_id(object_type: str, sequence_value: int) -> str:
    """Return a stable human-readable Engineering Object identifier."""
    normalized_type = object_type.upper()
    if normalized_type not in PREFIXES:
        raise ValueError(f"Unsupported Engineering Object type: {object_type}")
    if sequence_value < 1:
        raise ValueError("sequence_value must be greater than zero")
    return f"EO-{PREFIXES[normalized_type]}-{sequence_value:06d}"
