from subprocess import call
import tempfile
from rich.console import Console
from rich.markdown import Markdown
from cmd import Cmd

from .ai import EchoConversation


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


def vim_input(initial_text):
    with tempfile.NamedTemporaryFile(suffix=".txt") as tf:
        tf.write(bytes(initial_text, 'UTF-8'))
        tf.flush()
        call(['vim', '+set backupcopy=yes', tf.name])
        tf.seek(0)
        prompt = tf.read()
    return prompt.decode("utf-8")


if __name__ == "__main__":
    prompt = ChatUI()
    prompt.prompt = '>> '
    prompt.cmdloop("Starting chat")
