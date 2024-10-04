from pydantic import BaseModel

from top_assist.utils.tracer import ServiceNames, tracer

from ._client import ConfluenceClient


class ConfluenceSpaceInfo(BaseModel):
    """Confluence Space information.

    Attr:
        id: The ID of the space
        name: The name of the space in Confluence
        key: The key of the space in Confluence
        status: The status of the space (current, archived)
    """

    name: str
    key: str
    status: str


@tracer.wrap(service=ServiceNames.confluence.value)
def retrieve_space_list(status: str = "current") -> list[ConfluenceSpaceInfo]:
    """Retrieve list of spaces from confluence.

    Args:
        status (str): The status of the spaces to retrieve (current, archived)

    Returns:
        list[ConfluenceSpaceInfo]: List of ConfluenceSpaceInfo objects
    """
    client = ConfluenceClient()
    return [ConfluenceSpaceInfo(**space) for space in client.retrieve_space_list(status=status)]
