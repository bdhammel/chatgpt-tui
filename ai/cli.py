import argparse
import sys
import tempfile
from pathlib import Path

from rich.prompt import Prompt

from ai import database
from ai.ai import start_conversation
from ai.database import session
from ai.tui import Chat

ROOT = Path(__file__).absolute().parents[1]
DEFAULT_DB = ROOT / "db.json"


@session()
def save_agent(db):
    name = input("Enter a name for your agent")
    instructions = input("Enter instructions for your agent")
    agent = database.Agent(name=name, content=instructions)
    db.add(agent)
    db.commit()


def first_time_setup():
    id_ = Prompt.ask("Enter your organization id")
    api_key = Prompt.ask("Enter your api-key")
    metadata = database.MetaDataSchema.latest(id_=id_, api_key=api_key)
    session().setup(metadata)


def start_debug_chat():
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp_db:
        db_path = Path(tmp_db.name)

        session.use_database(db_path)
        metadata = database.MetaDataSchema.latest(id_=1, api_key=1)
        session().setup(metadata)

        convo = start_conversation(debug=True)
        app = Chat(conversation=convo)
        app.run()


def start_chat(db_path: Path):
    session.use_database(db_path)
    if not session().is_setup:
        first_time_setup()

    convo = start_conversation()
    app = Chat(conversation=convo)
    app.run()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    if args.debug:
        start_debug_chat()
    else:
        start_chat(args.db)


if __name__ == "__main__":
    sys.exit(main())
