import random

import pytest

from ai.database import (
    LATEST_VERSION,
    Connection,
    DBSchema,
    MetaDataSchema,
    add_agent,
    session,
)


def test_initial_setup(empty_db_file):
    db_file = empty_db_file
    sess = session.use_database(db_file)
    assert not sess.is_setup

    id_ = random.random()
    api_key = random.random()
    expected = DBSchema(version=LATEST_VERSION, id_=id_, api_key=api_key, agents=[])

    metadata = MetaDataSchema.latest(id_=id_, api_key=api_key)
    sess.setup(metadata)

    assert sess.is_setup

    actual = DBSchema.parse_file(db_file)
    assert actual.dict() == expected.dict()


@pytest.mark.usefixtures("active_session")
def test_context_handler():
    sess = session()
    db_path = sess.db_path
    assert sess.is_setup
    num_agents = 5

    with sess as db:
        for i in range(num_agents):
            add_agent(name=f"agent-{i}", instructions=i, db=db)
        expected = db.db.copy()
        db.commit()

    actual = DBSchema.parse_file(db_path)
    assert len(actual.agents) == num_agents
    assert actual.dict() == expected.dict()


@pytest.mark.usefixtures("active_session")
def test_data_not_saved_if_no_commit():
    sess = session()
    db_path = sess.db_path
    assert sess.is_setup

    with sess as db:
        add_agent(name="agent", instructions="dne", db=db)

    actual = DBSchema.parse_file(db_path)
    assert len(actual.agents) == 0


@pytest.mark.usefixtures("active_session")
def test_decorator():
    sess = session()
    db_path = sess.db_path
    num_agents = 5

    @sess
    def foo(bar, *, db):
        add_agent(name="agent", instructions=bar, db=db)
        expected = db.db.copy()
        db.commit()
        return expected

    for i in range(num_agents):
        expected = foo(i)

    actual = DBSchema.parse_file(db_path)
    assert len(actual.agents) == num_agents
    assert actual.dict() == expected.dict()


def test_assert_connection():
    conn = Connection()

    with pytest.raises(AssertionError):
        conn.commit()

    with pytest.raises(AssertionError):
        conn.add("foo")

    with pytest.raises(AssertionError):
        conn.dne
