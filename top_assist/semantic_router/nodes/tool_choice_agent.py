import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI

from top_assist.configuration import model_id_mini
from top_assist.semantic_router.tools import tools
from top_assist.semantic_router.types import RouterState

llm = ChatOpenAI(
    model=model_id_mini,
    temperature=0,
    max_retries=2,
)

prompt_template = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpfully assistant tasked with providing the best tool for the user's question."
        "You must choose only one tool that you think is the best for the user's question."
        "Begin!"
        "Question: {input}",
    )
])


def run_tool_choice_agent(state: RouterState) -> dict:
    """Choose the best tool for the user's question."""
    logging.debug("Current state in the tool choice agent", extra={"state": state})
    prompt = prompt_template.invoke({
        "input": state["prepared_question"],
    })

    model = llm.bind_tools(tools)
    response = model.invoke(prompt)

    logging.info("Model chose a tool", extra={"response": response})

    tool_call = response.tool_calls[0] if hasattr(response, "tool_calls") and response.tool_calls else None

    return {"messages": [response], "tool_call": tool_call}
