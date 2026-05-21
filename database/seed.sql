-- SYNTEXA DATABASE SEED
-- Execute após criar o banco: psql -d syntexa -f database/seed.sql

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    subscription_plan VARCHAR(50) DEFAULT 'free',
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de sessões de chat
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'Nova conversa',
    model_used VARCHAR(100) DEFAULT 'syntexa-large',
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de mensagens
CREATE TABLE IF NOT EXISTS conversation_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    model_used VARCHAR(100),
    provider VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de conhecimento (RAG)
CREATE TABLE IF NOT EXISTS knowledge_items (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500),
    question TEXT,
    answer TEXT NOT NULL,
    category VARCHAR(100),
    source VARCHAR(255),
    embedding VECTOR(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de preferências do usuário
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    pref_key VARCHAR(255) NOT NULL,
    pref_value TEXT,
    language VARCHAR(10) DEFAULT 'pt',
    subject VARCHAR(100),
    sentiment VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, pref_key)
);

-- Tabela de tokens de integração
CREATE TABLE IF NOT EXISTS integration_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    scopes JSONB DEFAULT '[]',
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de pagamentos
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    stripe_session_id VARCHAR(255),
    stripe_payment_intent_id VARCHAR(255),
    plan VARCHAR(50) NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'BRL',
    status VARCHAR(50) DEFAULT 'pending',
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    resource VARCHAR(255),
    detail TEXT,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_logs_session ON conversation_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_logs_user ON conversation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_category ON knowledge_items(category);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- Índice vetorial para RAG
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding ON knowledge_items USING ivfflat (embedding vector_cosine_ops);

-- Admin padrão (alterar senha em produção!)
INSERT INTO users (email, hashed_password, full_name, is_admin, is_verified, subscription_plan)
VALUES (
    'admin@syntexa.dev',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6', -- bcrypt de 'changeme123'
    'Administrador Syntexa',
    TRUE,
    TRUE,
    'master'
)
ON CONFLICT (email) DO NOTHING;

-- Seed de conhecimento básico
INSERT INTO knowledge_items (title, question, answer, category, source)
VALUES
('Sobre a Syntexa', 'O que é a Syntexa?', 'A Syntexa é uma plataforma de inteligência artificial brasileira desenvolvida para auxiliar em diversas áreas do conhecimento, incluindo programação, engenharia, ciências, jurídico e educação.', 'geral', 'docs'),
('Planos', 'Quais são os planos disponíveis?', 'Oferecemos planos Gratuito (120 mensagens/dia), Básico (R$ 39/mês), Médio (R$ 99/mês) e Master (R$ 199/mês). Também temos planos institucionais para escolas.', 'vendas', 'docs'),
('Privacidade', 'Meus dados são seguros?', 'Sim. A Syntexa opera com arquitetura soberana — seus dados não são compartilhados com terceiros. Utilizamos criptografia end-to-end e compliance LGPD.', 'seguranca', 'docs'),
('Como usar', 'Como começar a usar?', 'Basta acessar syntexabr.com.br, criar uma conta gratuita e começar a conversar. Não é necessário cartão de crédito para o plano gratuito.', 'suporte', 'docs')
ON CONFLICT DO NOTHING;

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
