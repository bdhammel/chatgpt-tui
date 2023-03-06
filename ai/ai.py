import json
import random
import asyncio
from functools import wraps
from pathlib import Path

import openai
import yaml
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class Usage(BaseModel):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


class session:
    def __init__(self):
        self.db_file = Path("db.json")
        self._db = None

    def __enter__(self):
        self._handler = open(self.db_file, "r+")
        self._db = json.load(self._handler)
        return self.db

    @property
    def db(self):
        return self._db

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._handler.seek(0)
        json.dump(self._db, self._handler)
        self._handler.close()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                res = func(*args, **kwargs, db=self.db)
                return res

        return wrapper


class _Conversation:
    PRICE_PER_TOKEN = 0.002 / 1000

    def __init__(self):
        self._conversation = []
        self.total_tokens = 0

    def who(self, persona: str):
        msg = Message(role="system", content=persona)
        self._conversation.append(msg.dict())

    async def ask(self, prompt: str) -> str:
        msg = Message(role="user", content=prompt)
        self._conversation.append(msg.dict())
        msg = await self._send(msg)
        return msg.content

    def _send(self, msg: Message) -> Message:
        raise NotImplementedError

    @property
    def total_cost(self) -> int:
        return self.total_tokens * self.PRICE_PER_TOKEN


class EchoConversation(_Conversation):
    async def _send(self, msg: Message) -> Message:
        num = random.random()
        await asyncio.sleep(num)
        msg = Message(role="Agent", content=f"mock response {num}")
        self._conversation.append(msg.dict())
        self.total_tokens += 0
        text_convo = "\n".join(
            f" - {m['role']}: {m['content']}" for m in self._conversation
        )
        return Message(role="Agent", content=text_convo)


class GPTConversation(_Conversation):
    PRICE_PER_TOKEN = 0.002 / 1000
    MODEL = "gpt-3.5-turbo"

    def __init__(self):
        super().__init__()
        with open("secrets.yaml") as f:
            secrets = yaml.safe_load(f)

        openai.organization = secrets["organization"]
        openai.api_key = secrets["api_key"]

    async def _send(self, msg: Message):
        res = await openai.ChatCompletion.acreate(
            model=self.MODEL, messages=self._conversation
        )
        msg, usage = parse_response(res)
        self._conversation.append(msg.dict())
        self.total_tokens += usage.total_tokens
        return msg


def start_conversation(debug=False):
    if debug:
        Conversation = EchoConversation
    else:
        Conversation = GPTConversation
    return Conversation()


@session()
def test(db):
    pass


def parse_response(res):
    msg = Message(**res["choices"][0]["message"])
    usage = Usage(**res["usage"])
    return msg, usage
