"""Load an optional local embedding model and score a small corpus."""

from functools import lru_cache
from math import sqrt

MODEL_NAME = "BAAI/bge-small-en-v1.5"


@lru_cache(maxsize=1)
def embedding_model():
    try:
        from fastembed import TextEmbedding
    except ImportError as exc:
        raise ValueError("Hybrid search requires uv sync --extra semantic") from exc
    return TextEmbedding(model_name=MODEL_NAME)


@lru_cache(maxsize=8)
def passage_vectors(passages: tuple[str, ...]):
    return tuple(embedding_model().passage_embed(passages))


def cosine(left, right) -> float:
    dot = sum(float(a) * float(b) for a, b in zip(left, right, strict=True))
    norm = sqrt(
        sum(float(value) ** 2 for value in left)
        * sum(float(value) ** 2 for value in right)
    )
    return dot / norm if norm else 0.0


def semantic_order(query: str, passages: tuple[str, ...]) -> list[int]:
    (query_vector,) = embedding_model().query_embed([query])
    scores = [
        (index, cosine(query_vector, vector))
        for index, vector in enumerate(passage_vectors(passages))
    ]
    return [
        index
        for index, score in sorted(scores, key=lambda pair: (-pair[1], pair[0]))
        if score >= 0.35
    ][:5]
