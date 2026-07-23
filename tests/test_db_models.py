import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import EngineeringObject, EngineeringObjectStatus, EngineeringObjectType, ObjectRelation

pytestmark = pytest.mark.skipif(
    not __import__("os").getenv("DEVHUB_TEST_DATABASE_URL"),
    reason="DEVHUB_TEST_DATABASE_URL is required for PostgreSQL integration tests",
)


@pytest.fixture()
def session():
    import os

    engine = create_engine(os.environ["DEVHUB_TEST_DATABASE_URL"])
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE SCHEMA IF NOT EXISTS core")
        Base.metadata.drop_all(connection)
        Base.metadata.create_all(connection)
    with Session(engine) as db_session:
        yield db_session
    with engine.begin() as connection:
        Base.metadata.drop_all(connection)


def make_object(eo_id: str, title: str) -> EngineeringObject:
    return EngineeringObject(
        id=uuid.uuid4(),
        eo_id=eo_id,
        object_type=EngineeringObjectType.PROJECT,
        title=title,
        status=EngineeringObjectStatus.ACTIVE,
    )


def test_create_objects_and_relation(session: Session):
    source = make_object("EO-PROJ-000001", "Source")
    target = make_object("EO-PROJ-000002", "Target")
    session.add_all([source, target])
    session.flush()
    session.add(ObjectRelation(source_id=source.id, target_id=target.id, relation_type="DERIVED_FROM"))
    session.commit()

    assert len(source.outgoing_relations) == 1
    assert source.outgoing_relations[0].target_id == target.id


def test_duplicate_eo_id_is_rejected(session: Session):
    session.add_all([
        make_object("EO-PROJ-000003", "First"),
        make_object("EO-PROJ-000003", "Duplicate"),
    ])
    with pytest.raises(IntegrityError):
        session.commit()
