from openai import APIConnectionError, APIStatusError, RateLimitError

from agents.llm import get_client
from config import settings

EMBEDDING_DIMENSIONS = 1536


def get_embedding_dimensions() -> int:
    return EMBEDDING_DIMENSIONS


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    response = get_client().embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


class EmbeddingError(Exception):
    """Raised when embedding fails with a user-friendly message."""


def embed_texts_safe(texts: list[str]) -> list[list[float]]:
    try:
        return embed_texts(texts)
    except RateLimitError as exc:
        raise EmbeddingError(
            "OpenRouter quota/rate limit exceeded. Check credits at "
            "https://openrouter.ai/settings/credits"
        ) from exc
    except APIStatusError as exc:
        raise EmbeddingError(f"Embedding API error ({exc.status_code}): {exc.message}") from exc
    except APIConnectionError as exc:
        raise EmbeddingError(f"Cannot reach OpenRouter API: {exc}") from exc
