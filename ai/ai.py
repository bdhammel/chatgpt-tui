import yaml
import random
import json
import openai
from rich.console import Console
from rich.markdown import Markdown
import tempfile
from pathlib import Path
from functools import wraps
from subprocess import call
from cmd import Cmd
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
        self.db_file = Path('db.json')
        self._db = None

    def __enter__(self):
        self._handler = open(self.db_file, 'r+')
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


def vim_input(initial_text):
    with tempfile.NamedTemporaryFile(suffix=".txt") as tf:
        tf.write(bytes(initial_text, 'UTF-8'))
        tf.flush()
        call(['vim', '+set backupcopy=yes', tf.name])
        tf.seek(0)
        prompt = tf.read()
    return prompt.decode("utf-8")


@session()
def test(db):
    pass


def parse_response(res):
    msg = Message(**res['choices'][0]['message'])
    usage = Usage(**res['usage'])
    return msg, usage


class Conversation:

    PRICE_PER_TOKEN = 0.002 / 1000

    def __init__(self):
        self._conversation = []
        self.total_tokens = 0

    def who(self, persona: str):
        msg = Message(role="system", content=persona)
        self._conversation.append(msg.dict())

    def ask(self, prompt: str) -> str:
        msg = Message(role="user", content=prompt)
        self._conversation.append(msg.dict())
        msg = self._send(msg)
        return msg.content

    def _send(self, msg: Message) -> Message:
        raise NotImplementedError

    @property
    def total_cost(self) -> int:
        return self.total_tokens * self.PRICE_PER_TOKEN


class EchoConversation(Conversation):
    def _send(self, msg: Message) -> Message:
        num = random.random()
        msg = Message(role='Agent', content=f'mock response {num}')
        self._conversation.append(msg.dict())
        self.total_tokens += 0
        text_convo = '\n'.join(f" - {m['role']}: {m['content']}" for m in self._conversation)
        return Message(role='Agent', content=text_convo)


class GPTConversation(Conversation):
    PRICE_PER_TOKEN = 0.002 / 1000

    def __init__(self):
        super().__init__()
        with open('secrets.yaml') as f:
            secrets = yaml.safe_load(f)

        openai.organization = secrets["organization"]
        openai.api_key = secrets["api_key"]

    def _send(self, msg: Message):
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self._conversation
        )
        msg, usage = parse_response(res)
        self._conversation.append(msg.dict())
        self.total_tokens += usage.total_tokens
        return msg


class ChatUI(Cmd):

    def __init__(self):
        self.console = Console()
        self.conversation = EchoConversation()
        super().__init__()

    def do_editor(self, args):
        prompt = vim_input(args)
        md = Markdown(prompt)
        self.console.print("-"*20 + " [bold red]User[/] " + "-"*20)
        self.console.print(md)
        reply = self.conversation.ask(prompt)

        self.render_reply(reply)

    def do_ask(self, args):
        reply = self.conversation.ask(args)
        self.render_reply(reply)

    def do_talk_to(self, persona):
        persona = "You are " + persona
        self.conversation.who(persona)

    def render_reply(self, reply):
        self.console.print("")
        self.console.print("-"*20 + " [bold red]Agent[/] " + "-"*20)
        md = Markdown(reply)
        self.console.print(md)
        self.console.print("")
        self.console.print(f"Price of conversation so far: [bold red]${self.conversation.total_cost:.3f}[/]")
        self.console.print("")

    def do_quit(self, args):
        raise SystemExit


if __name__ == "__main__":
    prompt = ChatUI()
    prompt.prompt = '>> '
    prompt.cmdloop("Starting chat")
