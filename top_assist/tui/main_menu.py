from top_assist.knowledge_base.importer import pull_updates
from top_assist.utils.metrics import start_metrics_server
from top_assist.utils.tracer import ServiceNames, tracer

from .assistants import tui_assistants_menu
from .confluence import tui_import_space


@tracer.wrap(service=ServiceNames.main_menu)
def main_menu() -> None:
    start_metrics_server()

    while True:
        print("\nMain Menu:")
        print("1. Load New Documentation Space")
        print("2. Manage or query assistants")
        print("3. Pull updates from Confluence")
        print("0. Cancel/Quit")
        choice = input("Enter your choice (0-3): ")

        if choice == "1":
            tui_import_space()

        elif choice == "2":
            tui_assistants_menu()

        elif choice == "3":
            print("Update changed on Confluence pages since last import.")
            pull_updates()

        elif choice == "0":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please enter 0, 1, 2, or 3.")
