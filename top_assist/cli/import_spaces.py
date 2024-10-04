import argparse

from top_assist.confluence.spaces import retrieve_space_list
from top_assist.knowledge_base.importer import import_confluence_space


def add_command(parser: argparse._SubParsersAction) -> None:
    description = "Import Confluence spaces"
    command = parser.add_parser("import_spaces", help=description, description=description)
    command.add_argument("spaces", nargs="+", help="Space keys to import")
    command.set_defaults(func=__exec)


def __exec(args: argparse.Namespace) -> None:
    spaces = {s.key: s.name for s in retrieve_space_list()}
    for key in args.spaces:
        name = spaces.get(key)
        if not name:
            print(f"Given space key ({key}) is not found, ignoring.")
            continue

        print(f"Importing space {key}: {name}")

        import_confluence_space(space_key=key, space_name=name)
