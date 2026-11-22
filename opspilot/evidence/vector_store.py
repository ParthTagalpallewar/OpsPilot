"""Persist content-addressed runbook vectors and search by cosine distance."""

import json
from hashlib import sha256

from opspilot.evidence.embeddings import MODEL_NAME, embedding_model, passage_vectors


def vector_literal(values) -> str:
    return json.dumps([float(value) for value in values], allow_nan=False)


def pgvector_order(dsn: str, query: str, passages: tuple[str, ...]) -> list[int]:
    try:
        import psycopg
    except ImportError as exc:
        raise ValueError("pgvector search requires uv sync --extra semantic") from exc

    keys = [sha256(text.encode()).hexdigest() for text in passages]
    passage_by_key = dict(zip(keys, passages, strict=True))
    (query_vector,) = embedding_model().query_embed([query])
    query_literal = vector_literal(query_vector)
    try:
        with psycopg.connect(dsn, connect_timeout=5, autocommit=True) as connection:
            existing = connection.execute(
                "SELECT content_hash FROM runbook_vectors "
                "WHERE model = %s AND content_hash = ANY(%s)",
                (MODEL_NAME, keys),
            ).fetchall()
            cached = {key for (key,) in existing}
            missing = [key for key in passage_by_key if key not in cached]
            if missing:
                vectors = passage_vectors(tuple(passage_by_key[key] for key in missing))
                with connection.transaction(), connection.cursor() as cursor:
                    cursor.executemany(
                        "INSERT INTO runbook_vectors (model, content_hash, embedding) "
                        "VALUES (%s, %s, %s::vector) ON CONFLICT DO NOTHING",
                        [
                            (MODEL_NAME, key, vector_literal(vector))
                            for key, vector in zip(missing, vectors, strict=True)
                        ],
                    )
            matches = connection.execute(
                "SELECT content_hash, embedding <=> %s::vector AS distance "
                "FROM runbook_vectors WHERE model = %s AND content_hash = ANY(%s) "
                "ORDER BY embedding <=> %s::vector LIMIT 10",
                (query_literal, MODEL_NAME, keys, query_literal),
            ).fetchall()
    except psycopg.Error as exc:
        raise ValueError(
            "Runbook vector database is unavailable or not initialized"
        ) from exc

    distances = {key: distance for key, distance in matches if distance <= 0.65}
    eligible = [i for i, key in enumerate(keys) if key in distances]
    return sorted(eligible, key=lambda index: (distances[keys[index]], index))[:5]
