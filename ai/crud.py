from ai import database
from ai.database import session


def new_agent(name, instructions):
    with session() as db:
        agent = database.add_agent(name=name, instructions=instructions, db=db)
        db.commit()
    return agent


def all_agents():
    with session() as db:
        agents = db.agents.copy()
    return agents


def get_credentials() -> database.Credentials:
    with session() as db:
        credentials = database.Credentials(id_=db.id_, api_key=db.api_key)
        return credentials
