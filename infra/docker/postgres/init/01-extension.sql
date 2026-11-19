-- Runs once, on first startup of an empty data volume.
-- Enables pgvector so embeddings can be stored in `vector` columns
-- and searched with HNSW indexes.
CREATE EXTENSION IF NOT EXISTS vector;