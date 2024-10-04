import logging
from typing import Annotated

from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from top_assist.open_ai.query import query_chatgpt as query_chatgpt_with_openai


@tool(return_direct=True)
def query_chatgpt(state: Annotated[dict, InjectedState]) -> AIMessage:
    """Query ChatGPT only when the user`s question explicitly contains one or more of the following keywords: "ChatGPT", "chat", "gpt", "openai".

    Ignore any queries that do not contain these specific keywords.

    Examples:
        - "ChatGPT: ..."
        - "Chat with GPT: ..."
        - "Ask gpt: ..."
        - "Find the answer using OpenAI: ..."
        - "Chatbot: ..."
        - "OpenAI: ..."
        - "Chat: ..."
    """
    logging.debug("Current state in the ChatGPT tool", extra={"state": state})
    answer = query_chatgpt_with_openai(question=state["prepared_question"], text_formatter=state["text_formatter"])
    logging.debug("ChatGPT answer", extra={"answer": answer})

    return AIMessage(
        content=answer.message,
        response_metadata={"assistant_thread_id": answer.assistant_thread_id},
    )
