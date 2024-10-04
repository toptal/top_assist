import logging
from typing import Annotated

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool, tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import InjectedState

from top_assist.configuration import model_id
from top_assist.utils.sentry_notifier import sentry_notify_exception

FALLBACK_MSG = "I'm sorry! Something went wrong with web search. Please try again later."


# Please see: https://github.com/langchain-ai/langchain/blob/master/docs/docs/integrations/providers/duckduckgo_search.mdx"
def ddg_search(question: str) -> str:
    """Use this tool as default."""
    return DuckDuckGoSearchRun().invoke(question)


def __create_agent(llm: ChatOpenAI, web_search_tools: list, prompt_template: ChatPromptTemplate) -> AgentExecutor:
    agent = create_tool_calling_agent(llm, web_search_tools, prompt_template)
    return AgentExecutor(
        agent=agent,
        tools=web_search_tools,
        max_iterations=5,
        handle_parsing_errors=True,  # Try to generate an answer even if the input is not parsed correctly
        verbose=False,  # Set to true to see the model thinking process
    )


llm = ChatOpenAI(model=model_id)
web_search_tools = [StructuredTool.from_function(ddg_search)]
prompt_template = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an AI assistant specializing in web searches and complex reasoning. Your task is to answer the following question."
        "Think about your next step to provide the best possible answer."
        "Question: {input}"
        "You MUST format your answer using Slack markdown:"
        "1) Do not use ### for headings. Use *bold* text instead."
        "2) Use only one asterisk for *bold* text and _italic_ text."
        "3) Divide the response into clear, concise paragraphs for better readability."
        "4) Highlight any code blocks using backticks."
        "Agent scratchpad: {agent_scratchpad}",
    )
])


@tool(return_direct=True)
def web_search(state: Annotated[dict, InjectedState]) -> AIMessage:
    """Use this tool to search the Internet when user question explicitly mentions the need for web or Internet search.

    Examples:
     - "Web search: ..."
     - "Search the Internet to find the answer: ..."
     - "Google it: ..."
     - "Search on the web: ..."
    """
    logging.debug("Current state in Web search tool", extra={"state": state})

    question = state["prepared_question"]
    try:
        agent_executor = __create_agent(llm, web_search_tools, prompt_template)
        answer = agent_executor.invoke({"input": question})
    except Exception as e:
        logging.exception("Error during web search tool execution", extra={"error": str(e)})
        sentry_notify_exception(e)
        answer = {"output": FALLBACK_MSG}

    logging.debug("Web search answer", extra={"answer": answer})
    text_formatter = state["text_formatter"]
    return AIMessage(content=text_formatter(answer["output"]))
