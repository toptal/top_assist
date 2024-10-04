import logging
from typing import cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from top_assist.configuration import model_id_mini
from top_assist.semantic_router.types import HistoryEntry, RouterState

llm = ChatOpenAI(model=model_id_mini, max_retries=2)


class PreparedQuestion(BaseModel):  # noqa: D101
    prepared_question: str


SYSTEM_PROMPT = (
    """
        You are an assistant specializing in the analysis and editing of user messages within a conversation thread. Your task is as follows:

        Divergent Messages: If the last user message deviates from the context of the conversation,
         return it exactly as it is, without making any changes.
        Contextual Messages: If the last user message aligns with the context, treat it as a command
        that must be prepared for another assistant. Make only minimal edits to ensure it is clear,
        coherent, and preserves every word's importance and the message`s original intent.
        Command Integrity: Ensure that the message is ready to be passed on to another assistant,
        where each word is critical for executing the intended command. Do not alter the meaning or omit any essential details.
        Your primary objective is to maintain the integrity and context of the conversation
        while ensuring the message is accurately prepared for further processing by another assistant.
        Examples:
        1)
        [{"role": "user", "content": "What is Ubuntu?"},
        {"role": "assistant", "content": "Ubuntu is a Linux distribution based on Debian."},
        {"role": "user", "content": "How do I install it?"}]
        return: "How do I install Ubuntu?"
        2)
        [{"role": "user", "content": "How I can check GraphQL schema for Platform?"},
        {"role": "assistant", "content": "You can check documentation for Platform."},
        {"role": "user", "content": "Where can I find it?"}]
        return: "Where can I find documentation for GraphQL schema for Platform?"
        3)
        [{"role": "user", "content": "What is Testbox?"},
        {"role": "assistant", "content": "Testbox is a testing framework for Platform."},
        {"role": "user", "content": "Ask a chatgpt about: Ask chatgpt about Ubuntu?"}]
        return: "Ask a chatgpt about: Ask chatgpt about Ubuntu?"
    """
).strip()


def run_question_generator(state: RouterState) -> dict:
    """Prepare the user question based on the conversation history."""
    logging.debug("Current state in the question generator", extra={"state": state})

    # If the question is the first in the thread, return it 'as is' without any changes.
    if len(state["history"]) == 1:
        prepared_question = state["history"][0]["content"]
        logging.info("Prepared question (skipped)", extra={"prepared_question": prepared_question})
        return {"prepared_question": prepared_question}

    messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
    messages.extend(__parse_history_for_langchain(state["history"]))

    prompt_template = ChatPromptTemplate.from_messages(messages)
    prepared_prompt = prompt_template.invoke(input={})

    llm_with_schema = llm.with_structured_output(method="json_schema", schema=PreparedQuestion)
    response = llm_with_schema.invoke(prepared_prompt)
    response = cast(PreparedQuestion, response)
    prepared_question = response.prepared_question

    logging.info("Prepared question", extra={"prepared_question": prepared_question})
    return {"prepared_question": prepared_question}


def __parse_history_for_langchain(history: list[HistoryEntry]) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for entry in history:
        if entry["role"] == "user":
            messages.append(HumanMessage(content=entry["content"]))
        elif entry["role"] == "assistant":
            messages.append(AIMessage(content=entry["content"]))

    logging.debug("Prepared history for the model", extra={"history": messages})
    return messages
