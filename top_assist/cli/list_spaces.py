import argparse

from top_assist.confluence.spaces import retrieve_space_list


def add_command(parser: argparse._SubParsersAction) -> None:
    description = "List Confluence spaces"
    command = parser.add_parser("list_spaces", description=description, help=description)
    command.set_defaults(func=__exec)


def __exec(_args: argparse.Namespace) -> None:
    spaces = retrieve_space_list()
    for i, space in enumerate(spaces):
        print(f"{i + 1}. {space.name} (Key: {space.key})")
