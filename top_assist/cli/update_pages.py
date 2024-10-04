import argparse

from top_assist.knowledge_base.importer import pull_updates
from top_assist.knowledge_base.stats_exporter import export_spaces_stats


def add_command(parser: argparse._SubParsersAction) -> None:
    description = "Update Confluence pages from imported spaces"
    command = parser.add_parser("update_pages", help=description, description=description)
    command.add_argument("--export-stats", help="Export spaces stats to Confluence", action="store_true")
    command.set_defaults(func=__exec)


def __exec(args: argparse.Namespace) -> None:
    print("Updating pages...")
    pull_updates()

    if args.export_stats:
        print("Exporting spaces stats to Confluence...")
        export_spaces_stats()
