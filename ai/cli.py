import argparse
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

from rich import print
from rich.prompt import Confirm, Prompt

from ai import ai, crud, database
from ai.database import session
from ai.tui import Chat

ROOT = Path.home() / ".chatgpt_tui"
DEFAULT_DB = ROOT / "db.json"

INITIAL_MENU = (
    "Speak with the default agent",
    "Select an agent from your saved list",
    "Create a new agent",
)


class Menu:
    def __init__(self, options: List, start_idx: int = 0):
        self.options = options
        self.start_idx = start_idx

    def get(self, i: int):
        return self.options[i - self.start_idx]

    @property
    def choices(self) -> List[str]:
        return [str(i) for i, _ in enumerate(self.options, start=self.start_idx)]

    def __rich__(self) -> str:
        display = [
            f"[bold magenta]{i}[/] - {option}"
            for i, option in enumerate(self.options, start=self.start_idx)
        ]
        return "\n".join(display)


def new_agent() -> database.AgentSchema:
    name = Prompt.ask("Enter a name for your agent")
    instructions = Prompt.ask("Enter instructions for your agent")
    agent = crud.new_agent(name, instructions)
    return agent


def first_time_setup():
    ok_to_setup = Confirm.ask(f"Adding folders to: {ROOT}.\nIs this okay?")
    if not ok_to_setup:
        raise SystemExit("Sorry about that")
    ROOT.mkdir()
    id_ = Prompt.ask("Enter your organization id")
    api_key = Prompt.ask("Enter your api-key")
    metadata = database.MetaDataSchema.latest(id_=id_, api_key=api_key)
    session().setup(metadata)


def start_debug_session():
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp_db:
        db_path = Path(tmp_db.name)

        session.use_database(db_path)
        metadata = database.MetaDataSchema.latest(id_=1, api_key=1)
        session().setup(metadata)

        agent = get_agent()
        convo = ai.EchoConversation(agent)
        convo.start(credentials=None)

        app = Chat(conversation=convo)
        app.run()


def start_chat(agent: database.AgentSchema):
    convo = ai.GPTConversation(who=agent)
    credentials = crud.get_credentials()
    convo.start(credentials)
    app = Chat(conversation=convo)
    app.run()


def init_session(db_path):
    session.use_database(db_path)
    if not session().is_setup:
        first_time_setup()


def get_agent() -> Optional[database.AgentSchema]:
    agents = {agent.name: agent for agent in crud.all_agents()}
    options = ["Create New Agent", "Default Agent", *agents.keys()]
    menu = Menu(options=options)
    print(menu)
    choice = Prompt.ask("Select an agent", choices=menu.choices)
    assert choice.isnumeric(), "Choice should have been an int, something went wrong"
    choice = int(choice)
    if choice == 0:
        agent = new_agent()
    elif choice == 1:
        agent = None
    else:
        agent_name = menu.get(choice)
        agent = agents.get(agent_name)

    return agent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enter into a debug mode that doesn't send info to openai",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="The path to a database you want to use if not the default",
    )
    args = parser.parse_args()

    if args.debug:
        start_debug_session()
        return

    init_session(args.db)
    agent = get_agent()
    start_chat(agent)


if __name__ == "__main__":
    sys.exit(main())
