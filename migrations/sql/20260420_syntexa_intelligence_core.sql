-- Syntexa Intelligence Core migration
-- PostgreSQL + pgvector

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    channel VARCHAR(32) NOT NULL DEFAULT 'web',
    source VARCHAR(64),
    language VARCHAR(16) DEFAULT 'pt-BR',
    is_anonymous BOOLEAN NOT NULL DEFAULT FALSE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES sessions(id),
    user_id BIGINT REFERENCES users(id),
    title VARCHAR(512),
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    detected_language VARCHAR(16),
    detected_subject VARCHAR(128),
    detected_sentiment VARCHAR(32),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id),
    user_id BIGINT REFERENCES users(id),
    role VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    language VARCHAR(16),
    subject VARCHAR(128),
    sentiment VARCHAR(32),
    model_used VARCHAR(64),
    prompt_tokens INT,
    completion_tokens INT,
    total_tokens INT,
    latency_ms DOUBLE PRECISION,
    embedding VECTOR(1536),
    metadata_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS model_runs (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id),
    message_id BIGINT REFERENCES messages(id),
    provider VARCHAR(64) NOT NULL,
    model_name VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'success',
    prompt_tokens INT,
    completion_tokens INT,
    total_tokens INT,
    latency_ms DOUBLE PRECISION,
    estimated_cost_usd DOUBLE PRECISION,
    error_message TEXT,
    metadata_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE IF EXISTS memory_items
    ADD COLUMN IF NOT EXISTS language VARCHAR(16),
    ADD COLUMN IF NOT EXISTS subject VARCHAR(128),
    ADD COLUMN IF NOT EXISTS sentiment VARCHAR(32),
    ADD COLUMN IF NOT EXISTS source VARCHAR(64) DEFAULT 'chat',
    ADD COLUMN IF NOT EXISTS embedding VECTOR(1536),
    ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ DEFAULT NOW();

CREATE TABLE IF NOT EXISTS feedback_events (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    conversation_id BIGINT REFERENCES conversations(id),
    message_id BIGINT REFERENCES messages(id),
    score INT,
    category VARCHAR(64),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_model_runs_conversation_id ON model_runs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_feedback_events_conversation_id ON feedback_events(conversation_id);

-- Exemplo de índice vetorial para busca semântica (ajuste listas/probes conforme carga):
-- CREATE INDEX IF NOT EXISTS idx_messages_embedding_ivfflat ON messages USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX IF NOT EXISTS idx_memory_items_embedding_ivfflat ON memory_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

COMMIT;
