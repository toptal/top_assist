from unittest.mock import MagicMock, call, patch

import openai
import pytest

from top_assist.open_ai.embeddings import embed_text

text = "This is a test text"
model = "gpt-3.5-turbo"
embedding_vector = [0.1, 0.2, 0.3]


def mock_create_success() -> MagicMock:
    return MagicMock(data=[MagicMock(embedding=embedding_vector)])


def mock_create_rate_limit_error() -> openai.RateLimitError:
    return openai.RateLimitError("Rate limit error", response=MagicMock(), body=None)


@patch("top_assist.open_ai.embeddings.client.embeddings.create")
@patch("time.sleep", new=MagicMock())
def test_embed_text_success(mock_create: MagicMock) -> None:
    """
    Test the embed_text function with a successful response.
    """
    mock_create.return_value = MagicMock(data=[MagicMock(embedding=embedding_vector)])

    result = embed_text(text, model)

    mock_create.assert_called_once_with(input=text, model=model)

    assert result == embedding_vector


@patch("top_assist.open_ai.embeddings.client.embeddings.create")
@patch("time.sleep", new=MagicMock())
def test_embed_text_with_attempts(mock_create: MagicMock) -> None:
    """
    Test the embed_text function with 2 rate limit errors and 1 success.
    """
    mock_create.side_effect = [
        mock_create_rate_limit_error(),
        mock_create_rate_limit_error(),
        mock_create_success(),
    ]

    result = embed_text(text, model)

    assert mock_create.mock_calls == [
        call(input=text, model=model),
        call(input=text, model=model),
        call(input=text, model=model),
    ]

    assert result == embedding_vector


@patch("top_assist.open_ai.embeddings.client.embeddings.create")
@patch("time.sleep", new=MagicMock())
def test_embed_text_with_attempts_exceeded(mock_create: MagicMock) -> None:
    """
    Test the embed_text function with 3 rate limit errors.
    """
    mock_create.side_effect = [
        mock_create_rate_limit_error(),
        mock_create_rate_limit_error(),
        mock_create_rate_limit_error(),
    ]

    with pytest.raises(openai.RateLimitError):
        embed_text(text, model)

    assert mock_create.mock_calls == [
        call(input=text, model=model),
        call(input=text, model=model),
        call(input=text, model=model),
    ]
