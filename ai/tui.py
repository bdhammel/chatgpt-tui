import subprocess
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum

from rich.console import Console, ConsoleOptions, RenderResult
from rich.markdown import Markdown
from rich.padding import Padding
from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, TextLog

from .ai import start_conversation

VIM_CMD = ["vim", "+set backupcopy=yes", "+normal G$" "+startinsert"]


class VimMode(Enum):
    INS = "insert"
    CMD = "command"


def chain_action(*args):
    def _chain():
        for action in args:
            action()

    return _chain


@dataclass
class TextBlock:
    speaker: str
    message: str

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Text(f"{self.speaker}", style="magenta")
        yield Markdown(self.message)


class Prompt(Input):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = VimMode.INS
        self.background_mode = {
            VimMode.INS: self.styles.background,
            VimMode.CMD: "blue",
        }

    def on_input_submitted(self, message: Input.Submitted) -> None:
        message.value = message.value
        self.value = ""

    def action_cmd_mode(self) -> None:
        self.mode = VimMode.CMD
        self.styles.background = self.background_mode[self.mode]

    def action_ins_mode(self) -> None:
        self.mode = VimMode.INS
        self.styles.background = self.background_mode[self.mode]

    async def on_key(self, event) -> None:
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            if self.mode is VimMode.INS:
                self.action_cmd_mode()
        elif self.mode is VimMode.CMD:
            event.prevent_default()
            event.stop()
            action = {
                "i": self.action_ins_mode,
                "a": chain_action(self.action_cursor_right, self.action_ins_mode),
                "A": chain_action(self.action_end, self.action_ins_mode),
                "h": self.action_cursor_left,
                "l": self.action_cursor_right,
                "w": self.action_cursor_right_word,
                "W": self.action_cursor_right_word,
                "b": self.action_cursor_left_word,
                "B": self.action_cursor_left_word,
                "x": self.action_delete_right,
                "X": self.action_delete_left,
                "D": self.action_delete_right_all,
                "$": self.action_end,
                "_": self.action_home,
                "0": self.action_home,
                "v": chain_action(self.action_vim, self.action_ins_mode),
            }.get(event.character, None)

            if action is not None:
                action()

    def action_vim(self) -> None:
        app = self.app
        assert app._driver is not None
        app._driver.stop_application_mode()
        initial_text = self.value
        try:
            with tempfile.NamedTemporaryFile(suffix=".txt") as tf:
                tf.write(bytes(initial_text, "UTF-8"))
                tf.flush()
                tf.seek(0, 2)
                # Need to create a separate backup copy
                # If we don't the edited text will not be saved into the current file
                subprocess.call([*VIM_CMD, tf.name])
                tf.seek(0)
                prompt = tf.read().decode("utf-8")
        finally:
            app.refresh()
            app._driver.start_application_mode()

        self.post_message_no_wait(Input.Submitted(sender=self, value=prompt))


class ConversationScreen(TextLog):
    def __init__(self, *args, **kwargs):
        super().__init__(wrap=True, highlight=True, markup=True, *args, **kwargs)

    async def append(self, message):
        self.write(Padding(message, (1, 1)))
        self.scroll_end(animate=True, duration=1)

    async def user_says(self, message):
        await self.append(TextBlock("User", message))

    async def agent_says(self, message):
        await self.append(TextBlock("Agent", message))


class Chat(App):
    CSS_PATH = "css/style.css"

    BINDINGS = [
        ("crtl+q", "quit", "close"),
    ]

    def __init__(self, debug, *args, **kwargs):
        self.conversation = start_conversation(debug=debug)
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield Header()
        yield ConversationScreen(id="chat")
        yield Prompt(placeholder="Prompt", classes="prompt", id="prompt")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        # Give the input focus, so we can start typing straight away
        self.query_one(Input).focus()

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        prompt = message.value
        await self.ask(prompt)

    async def ask(self, prompt: str) -> None:
        if not prompt:
            return
        convo = self.query_one("#chat", ConversationScreen)
        await convo.user_says(prompt)
        reply = await self.conversation.ask(prompt)
        await convo.agent_says(reply)


def main():
    app = Chat(debug=True)
    app.run()


if __name__ == "__main__":
    sys.exit(main())
