import logging
import re

from langgraph.graph import StateGraph

from top_assist.confluence.policy import PageAccessPolicy
from top_assist.semantic_router.nodes.question_generator import run_question_generator
from top_assist.semantic_router.nodes.tool_choice_agent import run_tool_choice_agent
from top_assist.semantic_router.nodes.tool_executor import run_tool_executor
from top_assist.semantic_router.types import HistoryEntry, RouterState, SemanticRouterResponse
from top_assist.utils.sentry_notifier import sentry_notify_exception

FALLBACK_MSG = "I'm sorry! Something went wrong. Please try again later."

TOOL_CHOICE_AGENT = "tool_choice_agent"
TOOL_EXECUTOR = "tools"
QUESTION_GENERATOR = "question_generator"

#  Please see LangGraph documentation for more information:
#  https://langchain-ai.github.io/langgraph/tutorials/
main_flow = StateGraph(RouterState)
main_flow.set_entry_point(QUESTION_GENERATOR)

main_flow.add_node(QUESTION_GENERATOR, run_question_generator)
main_flow.add_node(TOOL_CHOICE_AGENT, run_tool_choice_agent)
main_flow.add_node(TOOL_EXECUTOR, run_tool_executor)

main_flow.add_edge(QUESTION_GENERATOR, TOOL_CHOICE_AGENT)
main_flow.add_edge(TOOL_CHOICE_AGENT, TOOL_EXECUTOR)

main_flow.set_finish_point(TOOL_EXECUTOR)

main_graph = main_flow.compile()
# main_graph.get_graph().draw_mermaid_png(output_file_path="./top_assist/semantic_router/graph.png")  # Draw the graph to a file


def route(
    history: list[HistoryEntry],
    policy: PageAccessPolicy,
    assistant_thread_id: str | None = None,
) -> SemanticRouterResponse:
    """Route the user input to the appropriate tool and return the response message.

    Args:
        history: The history of the current Slack thread
        policy: The access policy to Confluence pages
        assistant_thread_id: The thread ID of the AI assistant if it is created during the current thread

    Returns:
        SemanticRouterResponse: The response message and the assistant thread ID
    """
    initial_state = RouterState(
        prepared_question="",
        tool_call=None,
        history=history,
        messages=[],
        policy=policy,
        assistant_thread_id=assistant_thread_id,
        text_formatter=__format_as_slack_markup,
    )

    try:
        result = main_graph.invoke(input=initial_state)
        logging.info("Routing result", extra={"result": result})

        last_message = result["messages"][-1]
        message = last_message.content
        assistant_thread_id = last_message.response_metadata.get("assistant_thread_id", None)
    except Exception as e:
        logging.exception("Semantic routing failed", extra={"initial_state": initial_state, "error": str(e)})
        sentry_notify_exception(e)
        # Always return a message to the user
        message = FALLBACK_MSG
        assistant_thread_id = None

    return SemanticRouterResponse(message=message, assistant_thread_id=assistant_thread_id)


def __format_as_slack_markup(response_text: str) -> str:
    """Base formatter for converting response text to Slack-compatible format."""
    # Convert bold formatting to Slack-compatible
    response_text = response_text.replace("**", "*")

    # Convert markdown links to Slack-compatible
    pattern = re.compile(r"\[([^]]+)]\((https?://[^)]+|http?://[^)]+)\)")

    def replace_link(match: re.Match[str]) -> str:
        text = match.group(1)
        link = match.group(2)
        return f"<{link}|{text}>"

    formatted_text = pattern.sub(replace_link, response_text)
    return formatted_text
