import backoff
import openai

from top_assist.configuration import open_ai_api_key
from top_assist.utils.tracer import ServiceNames, tracer

client = openai.OpenAI(api_key=open_ai_api_key)


@tracer.wrap(service=ServiceNames.open_ai.value)
@backoff.on_exception(backoff.expo, openai.RateLimitError, max_tries=3)
def embed_text(text: str, model: str) -> list[float]:
    """Embed the given text using the specified OpenAI model.

    Args:
        text: The text to embed
        model: The model to use for embedding

    Returns:
        list[float]: The embedding vector of the text
    """
    response = client.embeddings.create(input=text, model=model)
    embedding_vector = response.data[0].embedding
    return embedding_vector
