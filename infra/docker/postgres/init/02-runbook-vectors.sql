CREATE TABLE IF NOT EXISTS runbook_vectors (
    model TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    PRIMARY KEY (model, content_hash)
);

CREATE INDEX IF NOT EXISTS runbook_vectors_cosine_hnsw
    ON runbook_vectors USING hnsw (embedding vector_cosine_ops);
