from unittest.mock import Mock

import pytest

from app.db.models import EngineeringObjectType
from app.services.engineering_object_service import EngineeringObjectService


def test_create_object_rejects_empty_title_before_database_access():
    session = Mock()
    service = EngineeringObjectService(session)

    with pytest.raises(ValueError, match="Название инженерного объекта"):
        service.create_object(
            object_type=EngineeringObjectType.IDEA,
            title="   ",
        )

    session.add.assert_not_called()
    session.flush.assert_not_called()
