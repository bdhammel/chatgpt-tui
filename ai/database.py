import json
from functools import wraps
from io import TextIOWrapper
from pathlib import Path
from typing import List, Literal, Optional, Type

from pydantic import BaseModel, validator

LATEST_VERSION = 1


class MessageSchema(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class UsageSchema(BaseModel):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


class AgentSchema(BaseModel):
    name: str
    instructions: MessageSchema

    @validator("instructions")
    def role_must_be_system(cls, v):
        if v.role != "system":
            raise ValueError("Agent's role must be `system`")
        return v


class MetaDataSchema(BaseModel):
    api_key: str
    id_: str
    version: int

    @classmethod
    def latest(cls, **kwargs) -> Type["MetaDataSchema"]:
        return cls(version=LATEST_VERSION, **kwargs)


class DBSchema(MetaDataSchema):
    agents: List[AgentSchema]


class Connection:
    def __init__(self) -> None:
        self._commit: bool = False
        self.schema = DBSchema
        self.db: Optional[DBSchema] = None

    def assert_connected(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            assert self.db is not None
            return func(self, *args, **kwargs)

        return wrapper

    def initalize(self, metadata: MetaDataSchema):
        self.db = self.schema(**metadata.dict(), agents=[])
        self.commit()

    def connect(self, handler: TextIOWrapper):
        _db = json.load(handler)
        metadata = MetaDataSchema(**_db)
        # Only support latest version for now
        assert metadata.version == LATEST_VERSION
        self.db = self.schema(**_db)

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
    _db_path: Optional[Path] = None

    def __init__(self) -> None:
        self._connection: Optional[Connection] = None

    @classmethod
    def use_database(cls, db_path: Path):
        assert cls._db_path is None, f"Database {cls._db_path} is already being used"
        cls._db_path = db_path
        return cls()

    @property
    def db_path(self):
        assert self._db_path is not None, "A database file needs to be connected"
        return self._db_path

    @property
    def is_setup(self) -> bool:
        if not self.db_path.exists():
            return False

        with self as db:
            has_credentials = None not in [db.api_key, db.id_]

        return has_credentials

    def setup(self, metadata: MetaDataSchema):
        conn = Connection()
        conn.initalize(metadata)
        with open(self.db_path, "w") as f:
            conn.write(f)

    def _connect(self) -> Connection:
        assert self._connection is None, "Already connected"
        conn = Connection()
        conn.connect(self._handler)
        return conn

    def __enter__(self) -> Connection:
        self._handler = open(self.db_path, "r+")
        self._connection = self._connect()
        return self._connection

    def __exit__(self, exc_type, exc_value, exc_traceback):
        assert self._connection is not None, "No connection to exit"
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


def add_agent(name: str, instructions: str, db: Connection):
    db.add(
        AgentSchema(
            name=name, instructions=MessageSchema(role="system", content=instructions)
        )
    )
