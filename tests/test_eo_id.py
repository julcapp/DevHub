import pytest

from app.db.eo_id import format_eo_id


def test_format_eo_id():
    assert format_eo_id("project", 125) == "EO-PROJ-000125"
    assert format_eo_id("STAR", 21) == "EO-STAR-000021"


def test_format_eo_id_rejects_invalid_values():
    with pytest.raises(ValueError):
        format_eo_id("unknown", 1)
    with pytest.raises(ValueError):
        format_eo_id("PROJECT", 0)
