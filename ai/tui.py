from textual.app import App, ComposeResult
import subprocess
import tempfile
from textual.widgets import Header, Input, Markdown, Footer
from textual.containers import Content


class Chat(App):
    CSS_PATH = "css/style.css"

    BINDINGS = [
        ("v", "vim", "Open editor"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Content(id="results-container"):
            yield Markdown(id="chat")
        yield Input(placeholder="Prompt", classes="prompt", id="prompt")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        # Give the input focus, so we can start typing straight away
        self.query_one(Input).focus()

    async def action_vim(self) -> None:
        """An action to toggle dark mode."""
        self._driver.stop_application_mode()
        initial_text = 'test '
        try:
            with tempfile.NamedTemporaryFile(suffix=".txt") as tf:
                tf.write(bytes(initial_text, 'UTF-8'))
                tf.flush()
                tf.seek(0, whence=2)
                # Need to create a separate backup copy
                # If we don't the edited text will not be saved into the current file
                subprocess.call(['vim', '+set backupcopy=yes', tf.name])
                tf.seek(0)
                prompt = tf.read().decode("utf-8")
        finally:
            self.refresh()
            self._driver.start_application_mode()

        res = self.query_one("#chat", Markdown)
        await res.update(prompt)

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        if message.value:
            res = self.query_one("#chat", Markdown)
            await res.update(message.value)


if __name__ == "__main__":
    app = Chat()
    app.run()
