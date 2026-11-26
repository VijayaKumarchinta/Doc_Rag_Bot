-- pgvector must exist before any vector(n) column is declared.
-- This is database-scoped, so it only needs to run once per database.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS rag;

CREATE TABLE IF NOT EXISTS rag.documents (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename     TEXT NOT NULL,
    file_hash    TEXT NOT NULL UNIQUE,
    file_type    TEXT NOT NULL CHECK (file_type IN ('pdf','excel','csv')),
    status       TEXT NOT NULL DEFAULT 'pending',
    uploaded_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rag.chat_sessions (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rag.chat_messages (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES rag.chat_sessions(id) ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK (role IN ('user','assistant','system')),
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON rag.chat_messages(session_id);

CREATE TABLE IF NOT EXISTS rag.vector_records (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID NOT NULL REFERENCES rag.documents(id) ON DELETE CASCADE,
    content      TEXT NOT NULL,
    embedding    vector(1024) NOT NULL,
    metadata     JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vector_records_document
    ON rag.vector_records(document_id);

CREATE INDEX IF NOT EXISTS idx_vector_records_embedding
    ON rag.vector_records
    USING hnsw (embedding vector_cosine_ops);