import random
from pathlib import Path

import pytest

from ai.database import MetaDataSchema, session


@pytest.fixture(autouse=True)
def clear_session():
    yield
    session._db_path = None


@pytest.fixture
def empty_db_file(tmpdir):
    return Path(tmpdir / "db.json")


@pytest.fixture()
def db_file(empty_db_file):
    db_file = empty_db_file
    sess = session.use_database(db_file)
    id_ = random.random()
    api_key = random.random()
    metadata = MetaDataSchema.latest(id_=id_, api_key=api_key)
    sess.setup(metadata)
    return db_file


@pytest.fixture
def active_session(db_file):
    yield
    session._db_path = None
