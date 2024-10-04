import argparse

from top_assist.utils.tracer import ServiceNames, tracer

from .import_spaces import add_command as add_import_spaces_command
from .list_spaces import add_command as add_list_spaces_command
from .update_pages import add_command as add_update_pages_command


@tracer.wrap(service=ServiceNames.cli.value)
def run() -> None:
    parser = argparse.ArgumentParser(
        prog="bin/cli",
        description="Administer and configure TopAssist instance",
    )
    subparsers = parser.add_subparsers(required=True)

    add_import_spaces_command(subparsers)
    add_list_spaces_command(subparsers)
    add_update_pages_command(subparsers)

    args = parser.parse_args()
    args.func(args)


run()
