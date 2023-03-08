import asyncio
import random

import openai

from ai.database import Connection, MessageSchema, UsageSchema, session


class _Conversation:
    PRICE_PER_TOKEN = 0.002 / 1000

    def __init__(self):
        self._conversation = []
        self.total_tokens = 0

    async def ask(self, prompt: str) -> str:
        msg = MessageSchema(role="user", content=prompt)
        self._conversation.append(msg.dict())
        msg = await self._send(msg)
        return msg.content

    @property
    def total_cost(self) -> int:
        return self.total_tokens * self.PRICE_PER_TOKEN

    async def _send(self, msg: MessageSchema) -> MessageSchema:
        raise NotImplementedError

    def start(self):
        raise NotImplementedError


class EchoConversation(_Conversation):
    async def _send(self, msg: MessageSchema) -> MessageSchema:
        num = random.random()
        await asyncio.sleep(num)
        msg = MessageSchema(role="assistant", content=f"mock response {num}")
        self._conversation.append(msg.dict())
        self.total_tokens += 0
        template = " - {role}: {content}"
        text_convo = "\n".join(template.format(**m) for m in self._conversation)
        return MessageSchema(role="assistant", content=text_convo)

    @session()
    def start(self, db: Connection):
        pass


class GPTConversation(_Conversation):
    MODEL = "gpt-3.5-turbo"

    async def _send(self, msg: MessageSchema):
        res = await openai.ChatCompletion.acreate(
            model=self.MODEL, messages=self._conversation
        )
        msg, usage = parse_response(res)
        self._conversation.append(msg.dict())
        self.total_tokens += usage.total_tokens
        return msg

    @session()
    def start(self, db: Connection):
        openai.organization = db.id_
        openai.api_key = db.api_key


def start_conversation(debug=False):
    if debug:
        Conversation = EchoConversation
    else:
        Conversation = GPTConversation
    convo = Conversation()
    convo.start()
    return convo


def parse_response(res):
    msg = MessageSchema(**res["choices"][0]["message"])
    usage = UsageSchema(**res["usage"])
    return msg, usage
