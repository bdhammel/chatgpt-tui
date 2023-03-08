import argparse
import sys
import tempfile
from pathlib import Path
from typing import Optional

from rich import print
from rich.prompt import Confirm, Prompt

from ai import ai, crud, database
from ai.database import session
from ai.tui import Chat

ROOT = Path(__file__).absolute().parents[1]
DEFAULT_DB = ROOT / "db.json"


def new_agent() -> database.AgentSchema:
    name = Prompt.ask("Enter a name for your agent")
    instructions = Prompt.ask("Enter instructions for your agent")
    agent = crud.new_agent(name, instructions)
    return agent


def select_agent() -> Optional[database.AgentSchema]:
    agents = {agent.name: agent for agent in crud.all_agents()}
    print(*list(agents.keys()), sep="\n")
    name = Prompt.ask("Select an agent")
    agent = agents.get(name, None)
    if agent is None:
        make_new_agent = Confirm.ask("Create new agent?")
        if make_new_agent:
            agent = new_agent()
            print(f"Talking with agent {agent.name}")
        else:
            print("Talking with default agent")
    return agent


def first_time_setup():
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

        agent = select_agent()
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    if args.debug:
        start_debug_session()
        return

    init_session(args.db)
    agent = select_agent()
    start_chat(agent)


if __name__ == "__main__":
    sys.exit(main())
