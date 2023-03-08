import argparse
import sys

from rich.prompt import Prompt

from ai.database import MetaDataSchema, session
from ai.tui import Chat


def first_time_setup(id_=None, api_key=None):
    if id_ is None:
        id_ = Prompt.ask("Enter your organization id")
    if api_key is None:
        api_key = Prompt.ask("Enter your api-key")
    metadata = MetaDataSchema.latest(id_=id_, api_key=api_key)
    session().setup(metadata)


def start_debug_session():
    if not session().is_setup:
        first_time_setup()

    app = Chat(debug=True)
    app.run()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        start_debug_session()
        return

    if not session().is_setup:
        first_time_setup()

    app = Chat()
    app.run()


if __name__ == "__main__":
    sys.exit(main())
