-- Migration: Whatsapp SaaS Tables
-- Cria schema completo para gerenciar empresas, números, conversas e tokens

CREATE SCHEMA IF NOT EXISTS whatsapp;

-- 1. Empresas (Tenants)
CREATE TABLE whatsapp.companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  stripe_customer_id VARCHAR(255),
  plan VARCHAR(50) DEFAULT 'free', -- free, pro, enterprise
  tokens_limit INTEGER DEFAULT 100000,
  tokens_used INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Números WhatsApp por empresa
CREATE TABLE whatsapp.phone_numbers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES whatsapp.companies(id) ON DELETE CASCADE,
  phone_number_id VARCHAR(255) NOT NULL UNIQUE,
  display_number VARCHAR(20) NOT NULL,
  waba_id VARCHAR(255) NOT NULL,
  access_token VARCHAR(1024) NOT NULL,
  status VARCHAR(50) DEFAULT 'active', -- active, inactive, banned
  template_namespace VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Conversas / Threads
CREATE TABLE whatsapp.conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES whatsapp.companies(id) ON DELETE CASCADE,
  phone_number_id UUID NOT NULL REFERENCES whatsapp.phone_numbers(id) ON DELETE CASCADE,
  contact_phone VARCHAR(20) NOT NULL,
  contact_name VARCHAR(255),
  status VARCHAR(50) DEFAULT 'active', -- active, closed, blocked
  memory_summary TEXT, -- resumo da conversa para LLM
  last_message_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(phone_number_id, contact_phone)
);

-- 4. Mensagens
CREATE TABLE whatsapp.messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES whatsapp.conversations(id) ON DELETE CASCADE,
  direction VARCHAR(20) NOT NULL, -- inbound, outbound
  message_type VARCHAR(50) NOT NULL, -- text, image, audio, document, video
  content TEXT NOT NULL,
  media_url TEXT,
  media_type VARCHAR(100),
  wa_message_id VARCHAR(255),
  status VARCHAR(50) DEFAULT 'sent', -- sent, delivered, read, failed
  tokens_used INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tools / Ações executadas
CREATE TABLE whatsapp.executed_tools (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES whatsapp.conversations(id) ON DELETE CASCADE,
  tool_name VARCHAR(100) NOT NULL, -- pdf, xlsx, csv, docx, image_gen, etc
  input_data JSONB,
  output_data JSONB,
  file_url TEXT,
  file_type VARCHAR(100),
  tokens_used INTEGER DEFAULT 0,
  execution_time_ms INTEGER,
  status VARCHAR(50) DEFAULT 'success', -- success, failed, timeout
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Configurações por empresa (prompts, behavior, etc)
CREATE TABLE whatsapp.company_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL UNIQUE REFERENCES whatsapp.companies(id) ON DELETE CASCADE,
  system_prompt TEXT NOT NULL DEFAULT 'Você é um assistente IA profissional.',
  model_name VARCHAR(100) DEFAULT 'syntexa',
  max_tokens_per_message INTEGER DEFAULT 2048,
  temperature FLOAT DEFAULT 0.7,
  enable_pdf_export BOOLEAN DEFAULT TRUE,
  enable_excel_export BOOLEAN DEFAULT TRUE,
  enable_csv_export BOOLEAN DEFAULT TRUE,
  enable_docx_export BOOLEAN DEFAULT TRUE,
  enable_image_generation BOOLEAN DEFAULT FALSE,
  enable_web_search BOOLEAN DEFAULT FALSE,
  memory_enabled BOOLEAN DEFAULT TRUE,
  memory_max_interactions INTEGER DEFAULT 50,
  antispam_enabled BOOLEAN DEFAULT TRUE,
  antispam_messages_per_minute INTEGER DEFAULT 10,
  branding_logo_url TEXT,
  branding_color VARCHAR(7) DEFAULT '#007AFF',
  webhook_url TEXT, -- para notificar empresa de eventos
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Memória longa (contexto vectorizado)
CREATE TABLE whatsapp.memory_vectors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES whatsapp.companies(id) ON DELETE CASCADE,
  conversation_id UUID REFERENCES whatsapp.conversations(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding vector(1536),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX memory_vectors_embedding_idx ON whatsapp.memory_vectors USING hnsw (embedding vector_cosine_ops)
);

-- 8. Webhooks / Eventos
CREATE TABLE whatsapp.webhooks_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES whatsapp.companies(id) ON DELETE CASCADE,
  event_type VARCHAR(100) NOT NULL, -- message_received, message_sent, tool_executed, etc
  payload JSONB NOT NULL,
  http_status INTEGER,
  response_time_ms INTEGER,
  retries INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_conversations_company ON whatsapp.conversations(company_id);
CREATE INDEX idx_conversations_phone ON whatsapp.conversations(phone_number_id);
CREATE INDEX idx_messages_conversation ON whatsapp.messages(conversation_id);
CREATE INDEX idx_messages_created ON whatsapp.messages(created_at DESC);
CREATE INDEX idx_tools_conversation ON whatsapp.executed_tools(conversation_id);
CREATE INDEX idx_webhooks_company ON whatsapp.webhooks_log(company_id);

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION whatsapp.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER update_companies_timestamp
  BEFORE UPDATE ON whatsapp.companies
  FOR EACH ROW
  EXECUTE FUNCTION whatsapp.update_updated_at();

CREATE TRIGGER update_phone_numbers_timestamp
  BEFORE UPDATE ON whatsapp.phone_numbers
  FOR EACH ROW
  EXECUTE FUNCTION whatsapp.update_updated_at();

CREATE TRIGGER update_conversations_timestamp
  BEFORE UPDATE ON whatsapp.conversations
  FOR EACH ROW
  EXECUTE FUNCTION whatsapp.update_updated_at();

CREATE TRIGGER update_company_config_timestamp
  BEFORE UPDATE ON whatsapp.company_config
  FOR EACH ROW
  EXECUTE FUNCTION whatsapp.update_updated_at();

-- Comentários
COMMENT ON SCHEMA whatsapp IS 'Schema para SaaS WhatsApp com IA integrada';
COMMENT ON TABLE whatsapp.companies IS 'Empresas/Tenants do SaaS';
COMMENT ON TABLE whatsapp.phone_numbers IS 'Números WhatsApp Business (WABA)';
COMMENT ON TABLE whatsapp.conversations IS 'Conversas entre empresa e clientes';
COMMENT ON TABLE whatsapp.messages IS 'Mensagens individuais';
COMMENT ON TABLE whatsapp.executed_tools IS 'Ações IA executadas (PDF, Excel, etc)';
COMMENT ON TABLE whatsapp.company_config IS 'Configurações por empresa';
COMMENT ON TABLE whatsapp.memory_vectors IS 'Memória longa com embeddings pgvector';
COMMENT ON TABLE whatsapp.webhooks_log IS 'Log de eventos disparados';
