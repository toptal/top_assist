import json
import logging

from openai import OpenAI

from top_assist.configuration import open_ai_api_key
from top_assist.open_ai.assistants.manager import Assistant, AssistantManager
from top_assist.open_ai.assistants.templates import (
    base_assistant_template,
    qa_assistant_template,
)
from top_assist.open_ai.assistants.threads import add_user_message_and_complete


def tui_assistants_menu() -> None:
    """Provides interactive user interface for managing assistants."""
    client = OpenAI(api_key=open_ai_api_key)
    manager = AssistantManager(client)
    while True:
        print("\nUser Interaction Menu:")
        print("--------------------------------")
        print("1. Manage Assistants - View, modify, or delete assistants.")
        print("2. Create a New Q&A Assistant - Start the process of creating a new assistant.")
        print("3. Create a New Base Assistant - Start the process of creating a new assistant.")
        print("0. Exit - Exit the user interaction menu.")
        print("--------------------------------")

        choice = input("Enter your choice (0-3): ")
        if choice == "1":
            __management_menu(manager)
        elif choice == "2":
            created_assistant_id = manager.create_assistant(qa_assistant_template)
            print(f"New assistant created with ID: {created_assistant_id}")
        elif choice == "3":
            created_assistant_id = manager.create_assistant(base_assistant_template)
            print(f"New assistant created with ID: {created_assistant_id}")
        elif choice == "0":
            print("Exiting user interaction menu.")
            break
        else:
            print("Invalid choice. Please select a valid option.")


def __management_menu(manager: AssistantManager) -> None:
    assistants = manager.list_assistants()

    if not assistants:
        print("No assistants available.")
        return

    assistant_id = __select_assistant(manager, assistants)
    if assistant_id is None:
        return

    print("\nChoose an Action for the Assistant")
    print("------------------------------------")
    print("1. Chat - Chat with this assistant.")
    print("2. Update - Update this assistant's parameters.")
    print("3. Delete - Delete this assistant.")
    print("0. Cancel - Return to the previous menu.")
    print("------------------------------------")
    action = input("Choose an option (0-3): ")

    if action == "1":
        __chat_with_assistant(assistant_id)

    elif action == "2":
        __update_assistant_interactively(assistant_id, manager)

    elif action == "3":
        manager.delete_assistant(assistant_id)
        print("Assistant deleted successfully.")

    elif action == "0":
        # exit menu
        print("Operation canceled.")

    else:
        print("Invalid action.")


def __select_assistant(assistant_manager: AssistantManager, assistants: list[Assistant]) -> str | None:
    print("\nSelect an Assistant")
    print("-------------------")
    for index, assistant in enumerate(assistants, start=1):
        print(f"{index}. {assistant.name} (ID: {assistant.id})")
    print("0. Cancel - Return to the previous menu.")
    print("-------------------")

    assistant_index_str = input("Enter the number of the assistant you want to manage or '0' to cancel: ")
    if assistant_index_str == "0":
        print("Operation canceled.")
        return None

    try:
        assistant_index = int(assistant_index_str) - 1
        if 0 <= assistant_index < len(assistants):
            selected_assistant = assistants[assistant_index]
            assistant_id = selected_assistant.id
            details = assistant_manager.assistant_details(assistant_id)
            print(details)
            return assistant_id
        else:
            print("Invalid assistant number.")
            return None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None


def __chat_with_assistant(assistant_id: str) -> None:
    print("Welcome to the Assistant Chat!")
    thread_id = None

    while True:
        lines = []
        print("You: \nWrite your message, or write 'QUIT' to abort the chat.")
        while True:
            user_input = input()
            user_input = user_input.strip()
            if user_input.lower() == "quit":
                print("Exiting chat.")
                return  # Exit the entire chat function
            elif user_input.lower() == "done":
                break
            elif user_input:
                lines.append(user_input)

        if lines:
            user_message = "\n".join(lines)
            completion = add_user_message_and_complete(user_message, assistant_id=assistant_id, thread_id=thread_id)
            print("Assistant:")
            print(completion.message)
            thread_id = completion.thread_id
        else:
            print("No message entered.")

        print("\nContinue chatting, or type 'QUIT' to exit.")


def __update_assistant_interactively(assistant_id: str, manager: AssistantManager) -> None:
    params = manager.editable_params(assistant_id)
    for param_name, current_value in params.items():
        print(f"Current value of {param_name}: {current_value}")
        user_input = input(f"Press Enter to keep the current value or enter a new value for {param_name}: ").strip()
        if not user_input:
            continue

        if param_name in ["metadata", "tools"]:
            try:
                params[param_name] = json.loads(user_input)
            except json.JSONDecodeError:
                logging.exception("Invalid JSON for param. Keeping current value", extra={"param_name": param_name})
        else:
            params[param_name] = user_input

    manager.update_assistant(assistant_id, params)
    print("Assistant updated successfully.")
