from top_assist.confluence.spaces import ConfluenceSpaceInfo, retrieve_space_list
from top_assist.knowledge_base.importer import import_confluence_space


def tui_import_space() -> None:
    print("Loading new documentation space...")
    space = __choose_space()
    import_confluence_space(space_key=space.key, space_name=space.name)
    print()
    print(f"Space '{space.name}' retrieval and indexing complete.")


def __choose_space() -> ConfluenceSpaceInfo:
    """Prompt the user to choose a Confluence space from a list of available spaces."""
    spaces = retrieve_space_list()
    for i, space in enumerate(spaces):
        print(f"{i + 1}. {space.name} (Key: {space.key})")
    choice = int(input("Choose a space (number): ")) - 1
    return spaces[choice]
