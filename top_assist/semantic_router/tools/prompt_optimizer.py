import logging
from typing import Annotated, cast

import requests
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel

from top_assist.configuration import dify_api_endpoint, dify_prompt_optimizer_api_key, model_id_mini
from top_assist.utils.sentry_notifier import sentry_notify_exception

FALLBACK_MSG = "I'm sorry! Something went wrong with prompt optimizer. Please try again later."


class DifyResponseError(Exception):  # noqa: D101
    def __init__(self, details: str) -> None:
        super().__init__(f"The error occurred during the Dify response. Details: {details}")


class PreparedTask(BaseModel):
    """Prepared task data for Dify prompt optimizer.

    Attr:
        task: The task field containing the main task extracted from the user question.
        variables: The variables field containing the comma-separated list of variables.
    """

    task: str
    variables: str


llm = ChatOpenAI(model=model_id_mini, temperature=0)
SYSTEM_PROMPT = (
    """
    You are a question analyzer assistant.
    Your task is to understand a given user question, which contains a task related to prompt optimization along with potential input variables.
    Decompose the question into two parts:

    Identify and return the main task.
    Extract and list all variables as a comma-separated string. If no variables are provided, return an empty string.
    Please provide your response with JSON schema format:
    {{
        "task": "The task field containing the main task.",
        "variables": "The variables field containing the comma-separated list of variables."
    }}
    Question: {question}
    Begin!
    """
).strip()

prompt_template = ChatPromptTemplate.from_messages(["system", SYSTEM_PROMPT])
llm_with_schema = llm.with_structured_output(method="json_schema", schema=PreparedTask)


@tool(return_direct=True)
def query_prompt_optimizer(state: Annotated[dict, InjectedState]) -> AIMessage:
    """It is a AI Prompt Optimizer tool. Use it when the user explicitly asked about prompt optimization.

    This tool is based on Dify workflow.

    Examples:
        - "Optimize the prompt: ..."
        - "Prompt optimization: ..."
        - "Improve the prompt: ..."
        - "Optimize the question: ..."
        - "Optimize with Dify: ..."
    """
    logging.debug("Current state in the Dify tool", extra={"state": state})
    question = state["prepared_question"]

    try:
        prepared_prompt = prompt_template.invoke(input={"question": question})
        llm_response = llm_with_schema.invoke(prepared_prompt)
        prepared_task = cast(PreparedTask, llm_response)
        logging.debug("Dify task extraction result", extra={"prepared_task": prepared_task})

        answer = run_on_dify(prepared_task)
    except Exception as e:
        logging.exception(
            "Error during Dify tool execution", extra={"error_message": str(e), "error_class": e.__class__.__name__}
        )
        sentry_notify_exception(e)
        answer = FALLBACK_MSG

    return AIMessage(content=answer)


def run_on_dify(prepared_task: PreparedTask) -> str:
    """Call the Dify prompt optimizer API and return the result.

    Args:
        prepared_task (PreparedTask): The prepared task data for Dify

    Returns:
        str: The response from the Dify
    """
    headers = {
        "Authorization": f"Bearer {dify_prompt_optimizer_api_key}",
        "Content-Type": "application/json",
    }

    data = {
        "inputs": {"task": prepared_task.task, "variables": prepared_task.variables},
        "response_mode": "blocking",
        "user": "top_assist",
    }
    response = requests.post(dify_api_endpoint, headers=headers, json=data, timeout=300)
    logging.info("Dify prompt optimizer response", extra={"response": response.text})

    if response.status_code != requests.codes.ok:
        logging.error("Error during the Dify request", extra={"details": response.text})
        raise DifyResponseError(response.text)

    response_data = response.json()
    return response_data["data"]["outputs"]["result"]
