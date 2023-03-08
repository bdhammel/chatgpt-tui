from ai.database import session, MetaDataSchema, DBSchema, LATEST_VERSION, MessageSchema
import pytest
import random
from pathlib import Path


@pytest.fixture
def empty_db_file(tmpdir):
    return Path(tmpdir / 'db.json')


@pytest.fixture
def db_file(empty_db_file):
    db_file = empty_db_file
    sess = session(db_file)
    id_ = random.random()
    api_key = random.random()
    metadata = MetaDataSchema.latest(id_=id_, api_key=api_key)
    sess.setup(metadata)
    return db_file


def test_initial_setup(empty_db_file):
    db_file = empty_db_file
    sess = session(db_file)
    assert not sess.is_setup

    id_ = random.random()
    api_key = random.random()
    expected = DBSchema(version=LATEST_VERSION, id_=id_, api_key=api_key, agents=[])

    metadata = MetaDataSchema.latest(id_=id_, api_key=api_key)
    sess.setup(metadata)

    assert sess.is_setup

    actual = DBSchema.parse_file(db_file)
    assert actual.dict() == expected.dict()


def test_context_handler(db_file):

    sess = session(db_file)
    assert sess.is_setup
    num_agents = 5

    with sess as db:
        for i in range(num_agents):
            db.add(MessageSchema(role='system', content=i))
        expected = db.db.copy()
        db.commit()

    actual = DBSchema.parse_file(db_file)
    assert len(actual.agents) == num_agents
    assert actual.dict() == expected.dict()


def test_data_not_saved_if_no_commit(db_file):

    sess = session(db_file)
    assert sess.is_setup

    with sess as db:
        db.add(MessageSchema(role='system', content='dne'))

    actual = DBSchema.parse_file(db_file)
    assert len(actual.agents) == 0


def test_decorator(db_file):

    num_agents = 5

    @session(db_file)
    def foo(bar, *, db):
        db.add(MessageSchema(role='system', content=bar))
        expected = db.db.copy()
        db.commit()
        return expected

    for i in range(num_agents):
        expected = foo(i)

    actual = DBSchema.parse_file(db_file)
    assert len(actual.agents) == num_agents
    assert actual.dict() == expected.dict()
