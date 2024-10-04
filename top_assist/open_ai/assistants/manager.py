from typing import Any

from openai import OpenAI
from openai.types.beta.assistant import Assistant

from .templates import AssistantTemplate


class AssistantManager:
    """AssistantManager provides functionalities to manage the lifecycle of assistants.

    It includes CRUD, listing and loading assistants within the GPT-4-Turbo-Assistant environment.
    """

    def __init__(self, client: OpenAI):
        self.client = client

    def create_assistant(self, template: AssistantTemplate) -> str:
        response = self.client.beta.assistants.create(
            model=template.model,
            name=template.name,
            description=template.description,
            instructions=template.instructions,
        )
        return response.id

    def list_assistants(self) -> list[Assistant]:
        return self.client.beta.assistants.list().data

    def assistant_details(self, assistant_id: str) -> dict[str, Any]:
        assistant = self.__load_assistant(assistant_id)
        return assistant.model_dump()

    def editable_params(self, assistant_id: str) -> dict[str, Any]:
        assistant = self.__load_assistant(assistant_id)
        return {
            "name": assistant.name,
            "model": assistant.model,
            "instructions": assistant.instructions,
            "description": assistant.description,
            "metadata": assistant.metadata,
            "tools": assistant.tools,
        }

    def update_assistant(self, assistant_id: str, edited_params: dict[str, Any]) -> None:
        self.client.beta.assistants.update(assistant_id=assistant_id, **edited_params)

    def delete_assistant(self, assistant_id: str) -> None:
        self.client.beta.assistants.delete(assistant_id=assistant_id)

    def __load_assistant(self, assistant_id: str) -> Assistant:
        return self.client.beta.assistants.retrieve(assistant_id=assistant_id)
