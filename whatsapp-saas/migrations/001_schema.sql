-- Syntexa WhatsApp SaaS Schema
-- Created: 2026-05-28

CREATE SCHEMA IF NOT EXISTS whatsapp;

-- Companies (multi-tenant)
CREATE TABLE IF NOT EXISTS whatsapp.companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT,
    plan TEXT NOT NULL DEFAULT 'free',
    tokens_used INTEGER NOT NULL DEFAULT 0,
    tokens_limit INTEGER NOT NULL DEFAULT 10000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Phone numbers linked to Meta WABA
CREATE TABLE IF NOT EXISTS whatsapp.phone_numbers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES whatsapp.companies(id) ON DELETE CASCADE,
    phone_number_id TEXT NOT NULL UNIQUE,
    display_number TEXT,
    waba_id TEXT,
    access_token TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Company AI configuration
CREATE TABLE IF NOT EXISTS whatsapp.company_config (
    company_id UUID PRIMARY KEY REFERENCES whatsapp.companies(id) ON DELETE CASCADE,
    system_prompt TEXT DEFAULT 'Você é um assistente IA profissional para WhatsApp Business.',
    max_tokens_per_message INTEGER DEFAULT 500,
    temperature REAL DEFAULT 0.7,
    welcome_message TEXT,
    auto_reply_enabled BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Conversations
CREATE TABLE IF NOT EXISTS whatsapp.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES whatsapp.companies(id) ON DELETE CASCADE,
    phone_number_id UUID NOT NULL REFERENCES whatsapp.phone_numbers(id) ON DELETE CASCADE,
    contact_phone TEXT NOT NULL,
    contact_name TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    memory_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Messages
CREATE TABLE IF NOT EXISTS whatsapp.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES whatsapp.conversations(id) ON DELETE CASCADE,
    direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    message_type TEXT NOT NULL DEFAULT 'text',
    content TEXT,
    media_url TEXT,
    wa_message_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Executed tools (PDF/XLSX exports)
CREATE TABLE IF NOT EXISTS whatsapp.executed_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES whatsapp.conversations(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    input_data JSONB,
    status TEXT NOT NULL DEFAULT 'success',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Memory vectors (manual memory entries)
CREATE TABLE IF NOT EXISTS whatsapp.memory_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES whatsapp.conversations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_company ON whatsapp.conversations(company_id);
CREATE INDEX IF NOT EXISTS idx_conversations_phone ON whatsapp.conversations(phone_number_id);
CREATE INDEX IF NOT EXISTS idx_conversations_contact ON whatsapp.conversations(contact_phone);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON whatsapp.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON whatsapp.messages(created_at);
CREATE INDEX IF NOT EXISTS idx_memory_conversation ON whatsapp.memory_vectors(conversation_id);
CREATE INDEX IF NOT EXISTS idx_tools_conversation ON whatsapp.executed_tools(conversation_id);

-- Insert default config trigger
CREATE OR REPLACE FUNCTION whatsapp.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_conversations_updated
    BEFORE UPDATE ON whatsapp.conversations
    FOR EACH ROW EXECUTE FUNCTION whatsapp.update_updated_at();

CREATE TRIGGER trigger_company_config_updated
    BEFORE UPDATE ON whatsapp.company_config
    FOR EACH ROW EXECUTE FUNCTION whatsapp.update_updated_at();
