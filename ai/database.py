import json
from io import TextIOWrapper
from functools import wraps
from pathlib import Path
from typing import List, Optional, Literal

from pydantic import BaseModel

ROOT = Path(__file__).absolute().parents[1]
LATEST_VERSION = 1


class MessageSchema(BaseModel):
    role: Literal['user', 'assistant', 'system']
    content: str


class UsageSchema(BaseModel):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


class MetaDataSchema(BaseModel):
    api_key: str
    id_: str
    version: int

    @classmethod
    def latest(cls, **kwargs) -> 'MetaDataSchema':
        return cls(version=LATEST_VERSION, **kwargs)


class DBSchema(MetaDataSchema):
    agents: List[MessageSchema]


class Connection:

    def __init__(self):
        self._commit: bool = False
        self.schema = DBSchema
        self.db = None

    def initalize(self, metadata: MetaDataSchema):
        self.db = self.schema(**metadata.dict(), agents=[])
        self.commit()

    def connect(self, handler: TextIOWrapper):
        _db = json.load(handler)
        metadata = MetaDataSchema(**_db)
        # Only support latest version for now
        assert metadata.version == LATEST_VERSION
        self.db = self.schema(**_db)

    def assert_connected(func):
        def wrapper(self, *args, **kwargs):
            assert self.db is not None
            return func(self, *args, **kwargs)
        return wrapper

    @assert_connected
    def commit(self):
        self._commit = True

    @assert_connected
    def write(self, handler: TextIOWrapper):
        if self._commit:
            json.dump(self.db.dict(), handler, indent=2)

    @assert_connected
    def add(self, row: MessageSchema):
        self.agents.append(row)

    @assert_connected
    def __getattr__(self, attr: str):
        return getattr(self.db, attr)


class session:
    def __init__(self, db_file: Optional[Path] = None):
        if db_file is None:
            db_file = ROOT / "db.json"
        self.db_file = db_file
        self._connection: Optional[Connection] = None

    @property
    def is_setup(self) -> bool:
        if not self.db_file.exists():
            return False

        with self as db:
            has_credentials = None not in [db.api_key, db.id_]

        return has_credentials

    def setup(self, metadata: MetaDataSchema):
        conn = Connection()
        conn.initalize(metadata)
        with open(self.db_file, 'w') as f:
            conn.write(f)

    def _connect(self) -> Connection:
        assert self._connection is None
        conn = Connection()
        conn.connect(self._handler)
        return conn

    def __enter__(self) -> Connection:
        self._handler = open(self.db_file, "r+")
        self._connection = self._connect()
        return self._connection

    def __exit__(self, exc_type, exc_value, exc_traceback):
        assert self._connection is not None
        self._handler.seek(0)
        self._connection.write(self._handler)
        self._handler.close()
        self._connection = None

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self as db:
                res = func(*args, **kwargs, db=db)
                return res

        return wrapper
