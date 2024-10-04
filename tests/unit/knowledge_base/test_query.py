import json
from unittest.mock import MagicMock, create_autospec, patch

import pytest

from tests.unit.knowledge_base.factory import create_page_dto
from top_assist.configuration import confluence_base_url, qa_assistant_id, question_context_pages_count
from top_assist.confluence.policy import PageAccessPolicy
from top_assist.knowledge_base.query import FAILED_TO_ANSWER_MSG, KnowledgeBaseAnswer, query_knowledge_base
from top_assist.models.page_data import PageDataDTO
from top_assist.open_ai.assistants.threads import ThreadCompletion


@pytest.fixture()
def page1() -> PageDataDTO:
    return create_page_dto()


@pytest.fixture()
def page2() -> PageDataDTO:
    return create_page_dto()


@pytest.fixture()
def page3() -> PageDataDTO:
    return create_page_dto()


@pytest.fixture()
def mock_access_policy(mock_access_policy_class: MagicMock) -> MagicMock:
    mock_access_policy = create_autospec(PageAccessPolicy)
    mock_access_policy_class.return_value = mock_access_policy
    return mock_access_policy


@patch("top_assist.knowledge_base.query.db_pages.retrieve_relevant", autospec=True)
@patch("top_assist.knowledge_base.query.PageAccessPolicy", autospec=True)
@patch("top_assist.knowledge_base.query.add_user_message_and_complete", autospec=True)
def test_query_knowledge_base(
    mock_add_user_message_and_complete: MagicMock,
    mock_access_policy: MagicMock,
    mock_retrieve_relevant: MagicMock,
    page1: PageDataDTO,
    page2: PageDataDTO,
) -> None:
    # Given
    question = "That is my question"
    expected_thread_id = "thread_123456"
    ai_response = json.dumps({
        "comprehensive_answer": "This is an AI answer.",
        "summary": "AI summary.",
        "page_ids": [page1.page_id, page2.page_id],
    })
    expected_response = (
        "*Summary*\nAI summary.\n\n"
        "*Comprehensive Answer*\nThis is an AI answer.\n\n\n"
        "*Documents in context*\n\n"
        f"  •  <{confluence_base_url}wiki/spaces/{page1.space_key}/pages/{page1.page_id}|{page1.title}>\n"
        f"  •  <{confluence_base_url}wiki/spaces/{page2.space_key}/pages/{page2.page_id}|{page2.title}>\n"
    )

    mock_retrieve_relevant.return_value = [page1, page2]
    mock_access_policy.accessible_pages.return_value = [page1.page_id, page2.page_id]
    mock_add_user_message_and_complete.return_value = ThreadCompletion(
        message=ai_response, thread_id=expected_thread_id
    )

    # When
    res = query_knowledge_base(question=question, thread_id=None, access_policy=mock_access_policy)

    # Then
    mock_retrieve_relevant.assert_called_with(question, count=question_context_pages_count)
    mock_access_policy.accessible_pages.assert_called_with([page1.page_id, page2.page_id])
    mock_add_user_message_and_complete.assert_called_with(
        f"Here is the question and the context\n\n{question}\n\n"
        f"Context:\nDocument Title: {page1.title}\nSpace Key: {page1.space_key}\n\nspaceKey: {page1.space_key}\n"
        f"pageId: {page1.page_id}\ntitle: {page1.title}\nauthor: {page1.author}\ncreated_date: {page1.created_date.isoformat()}\n"
        f"last_updated: {page1.last_updated.isoformat()}\ncontent: {page1.content}\ncomments: {page1.comments}\n"
        f"Document Title: {page2.title}\nSpace Key: {page2.space_key}\n\nspaceKey: {page2.space_key}\n"
        f"pageId: {page2.page_id}\ntitle: {page2.title}\nauthor: {page2.author}\ncreated_date: {page2.created_date.isoformat()}\n"
        f"last_updated: {page2.last_updated.isoformat()}\ncontent: {page2.content}\ncomments: {page2.comments}",
        assistant_id=qa_assistant_id,
        thread_id=None,
        response_format={"type": "json_object"},
    )

    assert res == KnowledgeBaseAnswer(
        message=expected_response,
        assistant_thread_id=expected_thread_id,
    )


@patch("top_assist.knowledge_base.query.db_pages.retrieve_relevant", autospec=True)
@patch("top_assist.knowledge_base.query.PageAccessPolicy", autospec=True)
@patch("top_assist.knowledge_base.query.add_user_message_and_complete", autospec=True)
def test_query_knowledge_base_when_only_one_page_used(
    mock_add_user_message_and_complete: MagicMock,
    mock_access_policy: MagicMock,
    mock_retrieve_relevant: MagicMock,
    page1: PageDataDTO,
    page2: PageDataDTO,
) -> None:
    # Given
    question = "That is my question"
    expected_thread_id = "thread_123456"
    ai_response = json.dumps({
        "comprehensive_answer": "This is an AI answer.",
        "summary": "AI summary.",
        "page_ids": [page1.page_id],  # Only one page is used
    })
    expected_response = (
        "*Summary*\nAI summary.\n\n"
        "*Comprehensive Answer*\nThis is an AI answer.\n\n\n"
        "*Documents in context*\n\n"
        f"  •  <{confluence_base_url}wiki/spaces/{page1.space_key}/pages/{page1.page_id}|{page1.title}>\n"
    )

    mock_retrieve_relevant.return_value = [page1, page2]
    mock_access_policy.accessible_pages.return_value = [page1.page_id, page2.page_id]
    mock_add_user_message_and_complete.return_value = ThreadCompletion(
        message=ai_response, thread_id=expected_thread_id
    )

    # When
    res = query_knowledge_base(question=question, thread_id=None, access_policy=mock_access_policy)

    # Then
    mock_retrieve_relevant.assert_called_with(question, count=question_context_pages_count)
    mock_access_policy.accessible_pages.assert_called_with([page1.page_id, page2.page_id])
    mock_add_user_message_and_complete.assert_called_with(
        f"Here is the question and the context\n\n{question}\n\n"
        f"Context:\nDocument Title: {page1.title}\nSpace Key: {page1.space_key}\n\nspaceKey: {page1.space_key}\n"
        f"pageId: {page1.page_id}\ntitle: {page1.title}\nauthor: {page1.author}\ncreated_date: {page1.created_date.isoformat()}\n"
        f"last_updated: {page1.last_updated.isoformat()}\ncontent: {page1.content}\ncomments: {page1.comments}\n"
        f"Document Title: {page2.title}\nSpace Key: {page2.space_key}\n\nspaceKey: {page2.space_key}\n"
        f"pageId: {page2.page_id}\ntitle: {page2.title}\nauthor: {page2.author}\ncreated_date: {page2.created_date.isoformat()}\n"
        f"last_updated: {page2.last_updated.isoformat()}\ncontent: {page2.content}\ncomments: {page2.comments}",
        assistant_id=qa_assistant_id,
        thread_id=None,
        response_format={"type": "json_object"},
    )

    assert res == KnowledgeBaseAnswer(
        message=expected_response,
        assistant_thread_id=expected_thread_id,
    )


@patch("top_assist.knowledge_base.query.db_pages.retrieve_relevant", autospec=True)
@patch("top_assist.knowledge_base.query.PageAccessPolicy", autospec=True)
@patch("top_assist.knowledge_base.query.add_user_message_and_complete", autospec=True)
def test_query_knowledge_base_with_wrong_json(
    mock_add_user_message_and_complete: MagicMock,
    mock_access_policy: MagicMock,
    mock_retrieve_relevant: MagicMock,
    page1: PageDataDTO,
    page2: PageDataDTO,
) -> None:
    # Given (Assistants returns an incorrect JSON)
    question = "That is my question"
    expected_thread_id = "thread_123456"
    ai_response = '{"incorrect_json": "Some random text"}'
    expected_response = "Sorry, AI assistant failed to generate an answer. Please try again."

    mock_retrieve_relevant.return_value = [page1, page2]
    mock_access_policy.accessible_pages.return_value = [page1.page_id, page2.page_id]
    mock_add_user_message_and_complete.return_value = ThreadCompletion(
        message=ai_response, thread_id=expected_thread_id
    )

    # When
    res = query_knowledge_base(question=question, thread_id=None, access_policy=mock_access_policy)

    # Then
    mock_retrieve_relevant.assert_called_with(question, count=question_context_pages_count)
    mock_access_policy.accessible_pages.assert_called_with([page1.page_id, page2.page_id])
    mock_add_user_message_and_complete.assert_called_once()

    assert res == KnowledgeBaseAnswer(
        message=expected_response,
        assistant_thread_id=expected_thread_id,
    )


@patch("top_assist.knowledge_base.query.db_pages.retrieve_relevant", autospec=True)
@patch("top_assist.knowledge_base.query.PageAccessPolicy", autospec=True)
@patch("top_assist.knowledge_base.query.add_user_message_and_complete", autospec=True)
def test_query_knowledge_base_with_only_one_page_accessible(
    mock_add_user_message_and_complete: MagicMock,
    mock_access_policy: MagicMock,
    mock_retrieve_relevant: MagicMock,
    page1: PageDataDTO,
    page2: PageDataDTO,
    page3: PageDataDTO,
) -> None:
    # Given (page3 is not accessible for the user)
    question = "That is my question"
    expected_thread_id = "thread_123456"
    ai_response = json.dumps({
        "comprehensive_answer": "This is an AI answer.",
        "summary": "AI summary.",
        "page_ids": [page1.page_id, page2.page_id],
    })
    expected_response = (
        "*Summary*\nAI summary.\n\n"
        "*Comprehensive Answer*\nThis is an AI answer.\n\n\n"
        "*Documents in context*\n\n"
        f"  •  <{confluence_base_url}wiki/spaces/{page1.space_key}/pages/{page1.page_id}|{page1.title}>\n"
        f"  •  <{confluence_base_url}wiki/spaces/{page2.space_key}/pages/{page2.page_id}|{page2.title}>\n"
    )

    mock_retrieve_relevant.return_value = [page1, page2, page3]
    mock_access_policy.accessible_pages.return_value = [page1.page_id, page2.page_id]
    mock_add_user_message_and_complete.return_value = ThreadCompletion(
        message=ai_response, thread_id=expected_thread_id
    )

    # When
    res = query_knowledge_base(question=question, thread_id=None, access_policy=mock_access_policy)

    # Then
    mock_retrieve_relevant.assert_called_with(question, count=question_context_pages_count)
    mock_access_policy.accessible_pages.assert_called_with([page1.page_id, page2.page_id, page3.page_id])
    mock_add_user_message_and_complete.assert_called_once()

    assert res == KnowledgeBaseAnswer(
        message=expected_response,
        assistant_thread_id=expected_thread_id,
    )


@patch("top_assist.knowledge_base.query.db_pages.retrieve_relevant", autospec=True)
@patch("top_assist.knowledge_base.query.PageAccessPolicy", autospec=True)
@patch("top_assist.knowledge_base.query.add_user_message_and_complete", autospec=True)
def test_query_knowledge_base_when_question_in_thread(
    mock_add_user_message_and_complete: MagicMock,
    mock_access_policy: MagicMock,
    mock_retrieve_relevant: MagicMock,
    page1: PageDataDTO,
    page2: PageDataDTO,
) -> None:
    # Given
    question = "That is my question in the thread"
    expected_thread_id = "thread_123456"
    expected_response = "This is an AI answer."
    ai_response = json.dumps({
        "comprehensive_answer": expected_response,
        "summary": "AI summary.",
        "page_ids": [page1.page_id, page2.page_id],
    })

    mock_retrieve_relevant.return_value = [page1, page2]
    mock_access_policy.accessible_pages.return_value = [page1.page_id, page2.page_id]
    mock_add_user_message_and_complete.return_value = ThreadCompletion(
        message=ai_response, thread_id=expected_thread_id
    )

    # When
    res = query_knowledge_base(question=question, thread_id=expected_thread_id, access_policy=mock_access_policy)

    # Then
    mock_retrieve_relevant.assert_called_with(question, count=question_context_pages_count)
    mock_access_policy.accessible_pages.assert_called_with([page1.page_id, page2.page_id])
    mock_add_user_message_and_complete.assert_called_with(
        f"Here is the question and the context\n\n{question}\n\n"
        f"Context:\nDocument Title: {page1.title}\nSpace Key: {page1.space_key}\n\nspaceKey: {page1.space_key}\n"
        f"pageId: {page1.page_id}\ntitle: {page1.title}\nauthor: {page1.author}\ncreated_date: {page1.created_date.isoformat()}\n"
        f"last_updated: {page1.last_updated.isoformat()}\ncontent: {page1.content}\ncomments: {page1.comments}\n"
        f"Document Title: {page2.title}\nSpace Key: {page2.space_key}\n\nspaceKey: {page2.space_key}\n"
        f"pageId: {page2.page_id}\ntitle: {page2.title}\nauthor: {page2.author}\ncreated_date: {page2.created_date.isoformat()}\n"
        f"last_updated: {page2.last_updated.isoformat()}\ncontent: {page2.content}\ncomments: {page2.comments}",
        assistant_id=qa_assistant_id,
        thread_id=expected_thread_id,
        response_format={"type": "json_object"},
    )

    assert res == KnowledgeBaseAnswer(
        message=expected_response,
        assistant_thread_id=expected_thread_id,
    )


@patch("top_assist.knowledge_base.query.logging", autospec=True)
@patch("top_assist.knowledge_base.query.db_pages.retrieve_relevant", autospec=True)
@patch("top_assist.knowledge_base.query.PageAccessPolicy", autospec=True)
@patch("top_assist.knowledge_base.query.add_user_message_and_complete", autospec=True)
def test_query_knowledge_base_when_invalid_json(
    mock_add_user_message_and_complete: MagicMock,
    mock_access_policy: MagicMock,
    mock_retrieve_relevant: MagicMock,
    mock_logging: MagicMock,
    page1: PageDataDTO,
    page2: PageDataDTO,
) -> None:
    # Given
    question = "That is my question"
    expected_thread_id = "thread_123456"
    ai_response = "I'm a string, not a JSON"
    expected_response = FAILED_TO_ANSWER_MSG

    mock_retrieve_relevant.return_value = [page1, page2]
    mock_access_policy.accessible_pages.return_value = [page1.page_id, page2.page_id]
    mock_add_user_message_and_complete.return_value = ThreadCompletion(
        message=ai_response, thread_id=expected_thread_id
    )

    # When
    res = query_knowledge_base(question=question, thread_id=None, access_policy=mock_access_policy)

    # Then
    mock_retrieve_relevant.assert_called_with(question, count=question_context_pages_count)
    mock_access_policy.accessible_pages.assert_called_with([page1.page_id, page2.page_id])
    mock_add_user_message_and_complete.assert_called_once()
    mock_logging.exception.assert_called_with("Assistant response is not a valid JSON", extra={"response": ai_response})

    assert res == KnowledgeBaseAnswer(
        message=expected_response,
        assistant_thread_id=expected_thread_id,
    )
