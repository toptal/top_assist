import json
import logging
from collections.abc import Callable
from dataclasses import dataclass

import top_assist.database.pages as db_pages
from top_assist.configuration import qa_assistant_id, question_context_pages_count
from top_assist.confluence.policy import PageAccessPolicy
from top_assist.models.page_data import PageDataDTO
from top_assist.open_ai.assistants.threads import add_user_message_and_complete
from top_assist.utils.sentry_notifier import sentry_notify_issue
from top_assist.utils.tracer import ServiceNames, tracer

FAILED_TO_ANSWER_MSG = "Sorry, AI assistant failed to generate an answer. Please try again."


@dataclass
class KnowledgeBaseAnswer:  # noqa: D101
    message: str
    assistant_thread_id: str


@tracer.wrap(service=ServiceNames.knowledge_base.value)
def query_knowledge_base(
    *,
    question: str,
    thread_id: str | None = None,
    access_policy: PageAccessPolicy,
    text_formatter: Callable[[str], str] = lambda text: text,
) -> KnowledgeBaseAnswer:
    """Ask assistant a question using documents related to context query as a context."""
    log_page_ids = None
    try:
        pages = db_pages.retrieve_relevant(question, count=question_context_pages_count)
        log_page_ids = [page.page_id for page in pages]
        logging.debug("Building context from pages", extra={"log_page_ids": log_page_ids})
        allowed_pages = __filter_pages_by_access(pages, access_policy)

        context = __format_pages_as_context(allowed_pages)
        formatted_question = f"Here is the question and the context\n\n{question}\n\nContext:\n{context}"

        completion = add_user_message_and_complete(
            formatted_question,
            assistant_id=qa_assistant_id,
            thread_id=thread_id,
            response_format={"type": "json_object"},
        )
        formatted_message = __format_assistant_response(completion.message, allowed_pages, text_formatter, thread_id)

        return KnowledgeBaseAnswer(
            message=formatted_message,
            assistant_thread_id=completion.thread_id,
        )
    except Exception:
        logging.exception("Error processing assistant query", extra={"page_ids": log_page_ids, "thread_id": thread_id})
        raise


def __add_pages_links(allowed_pages: list[PageDataDTO], used_pages: list[str]) -> str:
    if not used_pages:
        return ""

    links = "\n*Documents in context*\n\n"
    for page in allowed_pages:
        if page.page_id in used_pages:
            links += f"  •  <{page.url()}|{page.title}>\n"

    return links


def __format_pages_as_context(
    pages: list[PageDataDTO],
    max_length: int = 30000,
    truncation_label: str = " [Content truncated due to size limit.]",
) -> str:
    """Formats specified files as a context string for referencing in responses.

    Ensuring the total context length does not exceed the specified maximum length.
    """
    context: list[str] = []
    for page in pages:
        title = page.title
        space_key = page.space_key
        file_content = page.format_for_llm()
        page_data = f"Document Title: {title}\nSpace Key: {space_key}\n\n{file_content}"

        # Truncate and stop if the total length exceeds the maximum allowed
        if len(context) + len(page_data) > max_length:
            available_space = max_length - len(context) - len(truncation_label)
            truncated_data = page_data[:available_space] + truncation_label
            context.append(truncated_data)
            break

        context.append(page_data)
    return "\n".join(context)


def __format_assistant_response(
    response: str, allowed_pages: list[PageDataDTO], text_formatter: Callable[[str], str], thread_id: str | None
) -> str:
    try:
        json_response = json.loads(response)
    except json.JSONDecodeError:
        logging.exception("Assistant response is not a valid JSON", extra={"response": response})
        sentry_notify_issue("Assistant response is not a valid JSON", extra={"response": response})
        return FAILED_TO_ANSWER_MSG

    message = ""
    summary = str(json_response.get("summary", ""))
    comprehensive_answer = str(json_response.get("comprehensive_answer", ""))

    if not summary and not comprehensive_answer:
        logging.warning("Assistant failed to generate a correct JSON", extra={"response": response})
        return FAILED_TO_ANSWER_MSG

    if not thread_id:
        # If the thread_id is not present, we consider the response as a first message
        used_page_ids = [str(page_id) for page_id in json_response.get("page_ids", [])]

        if summary:
            message = f"*Summary*\n{text_formatter(summary)}\n\n"
        if comprehensive_answer:
            message += f"*Comprehensive Answer*\n{text_formatter(comprehensive_answer)}\n\n"
        if allowed_pages:
            message += __add_pages_links(allowed_pages, used_page_ids)
    else:
        # Format the response as a follow-up message in the same thread just with the comprehensive answer
        message = text_formatter(json_response.get("comprehensive_answer", json_response.get("summary", "")))

    return message


def __filter_pages_by_access(pages: list[PageDataDTO], access_policy: PageAccessPolicy) -> list[PageDataDTO]:
    page_ids = [page.page_id for page in pages]
    allowed_page_ids = access_policy.accessible_pages(page_ids)
    allowed_pages = [page for page in pages if page.page_id in allowed_page_ids]
    logging.info("Allowed pages", extra={"allowed_page_ids": allowed_page_ids})
    return allowed_pages
