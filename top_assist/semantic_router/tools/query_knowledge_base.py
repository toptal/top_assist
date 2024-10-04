import logging
from typing import Annotated

from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from top_assist.knowledge_base.query import query_knowledge_base as query_confluence_knowledge_base


@tool(return_direct=True)
def query_knowledge_base(state: Annotated[dict, InjectedState]) -> AIMessage:
    """Use this tool by default for cases where other tools are less suitable based on keywords.

    It queries the Confluence Knowledge Base for answers to the user's questions.
    The Knowledge Base is part of TopTal internal Confluence system, containing articles and documents about the company's products, services, policies, and procedures.
    """
    logging.debug("Current state in the Knowledge Base tool", extra={"state": state})
    answer = query_confluence_knowledge_base(
        question=state["prepared_question"],
        thread_id=state["assistant_thread_id"],
        access_policy=state["policy"],
        text_formatter=state["text_formatter"],
    )
    logging.debug("Knowledge base answer", extra={"answer": answer})

    # The tool response must be a BaseMessage or a string.
    # We cannot update the global State inside the tool, so we return additional metadata within the AIMessage.
    text_formatter = state["text_formatter"]
    return AIMessage(
        content=text_formatter(answer.message),
        response_metadata={"assistant_thread_id": answer.assistant_thread_id},
    )
