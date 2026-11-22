"""Rank Markdown runbook sections by keyword and optional semantic relevance."""

import os
import re
import sqlite3
from collections import defaultdict
from contextlib import closing
from hashlib import sha256
from pathlib import Path

from opspilot.evidence.embeddings import MODEL_NAME, semantic_order
from opspilot.evidence.vector_store import pgvector_order

SECTION = re.compile(r"^## (.+)$", re.MULTILINE)
WORD = re.compile(r"[a-z0-9]+")


def sections(path: Path):
    document = path.read_text(encoding="utf-8")
    headings = list(SECTION.finditer(document))
    for index, heading in enumerate(headings):
        end = (
            headings[index + 1].start() if index + 1 < len(headings) else len(document)
        )
        excerpt = document[heading.end() : end].strip()
        if excerpt:
            line = document.count("\n", 0, heading.start()) + 1
            yield path.name, line, heading[1].strip(), excerpt


def keyword_order(chunks: list[tuple], query: str) -> list[int]:
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute(
            "CREATE VIRTUAL TABLE chunks USING fts5("
            "source UNINDEXED, line UNINDEXED, heading, excerpt, tokenize='porter')"
        )
        connection.executemany("INSERT INTO chunks VALUES (?, ?, ?, ?)", chunks)
        matches = connection.execute(
            "SELECT rowid FROM chunks WHERE chunks MATCH ? "
            "ORDER BY bm25(chunks, 0, 0, 3, 1), source, line LIMIT 5",
            (query,),
        ).fetchall()
    return [row_id - 1 for (row_id,) in matches]


def retrieve_runbooks(directory: Path, service: str, symptom: str) -> list[dict]:
    terms = sorted(set(WORD.findall(symptom.lower())) - {service})
    if WORD.fullmatch(service) is None or not terms:
        return []
    query = f'"{service}" AND (' + " OR ".join(f'"{term}"' for term in terms) + ")"
    chunks = [
        chunk for file in sorted(directory.glob("*.md")) for chunk in sections(file)
    ]
    if not chunks:
        return []

    keywords = keyword_order(chunks, query)
    semantic = []
    hybrid = os.environ.get("OPSPILOT_RUNBOOK_SEARCH") == "hybrid"
    vector_dsn = os.environ.get("OPSPILOT_VECTOR_DSN") if hybrid else None
    if hybrid:
        candidates = [
            (index, f"{heading}\n{excerpt}")
            for index, (_, _, heading, excerpt) in enumerate(chunks)
            if service in WORD.findall(f"{heading} {excerpt}".lower())
        ]
        if candidates:
            indexes, passages = zip(*candidates, strict=True)
            semantic_query = f"{service}: {symptom}"
            ranked = (
                pgvector_order(vector_dsn, semantic_query, passages)
                if vector_dsn
                else semantic_order(semantic_query, passages)
            )
            semantic = [indexes[index] for index in ranked]

    scores = defaultdict(float)
    for ranking in (keywords, semantic):
        for rank, index in enumerate(ranking, start=1):
            scores[index] += 1 / (60 + rank)
    if not scores:
        return []

    best = max(
        scores,
        key=lambda index: (
            scores[index],
            -keywords.index(index) if index in keywords else -len(keywords),
            -index,
        ),
    )
    source, line, heading, excerpt = chunks[best]
    signature = f"{source}:{line}\n{heading}\n{excerpt}".encode()
    record = {
        "id": f"ev_runbook_{sha256(signature).hexdigest()}",
        "type": "runbook",
        "source": source,
        "line": line,
        "heading": heading,
        "excerpt": excerpt,
        "query": query,
    }
    if hybrid:
        record["retrieval"] = {
            "mode": "hybrid",
            "model": MODEL_NAME,
            "vector_store": "pgvector" if vector_dsn else "memory",
            "semantic_query": f"{service}: {symptom}",
            "keyword_rank": keywords.index(best) + 1 if best in keywords else None,
            "semantic_rank": semantic.index(best) + 1 if best in semantic else None,
        }
    return [record]
