from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from vereda_backend.db.session import Base

try:
    from pgvector.sqlalchemy import Vector  # type: ignore
except Exception:  # pragma: no cover
    Vector = None  # type: ignore

# Dimensão fixa da coluna pgvector (migração); embeddings de outro tamanho vão só em embedding_json.
EMBEDDING_VECTOR_DIM = 1536


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    full_name = Column(String(255), nullable=True)
    username = Column(String(64), unique=True, index=True, nullable=True)
    avatar_url = Column(Text, nullable=True)
    document = Column(String(32), unique=True, index=True, nullable=True)
    cep = Column(String(16), nullable=True)
    state = Column(String(64), nullable=True)
    city = Column(String(128), nullable=True)
    address_line = Column(String(255), nullable=True)
    address_number = Column(String(32), nullable=True)
    address_complement = Column(String(255), nullable=True)
    subscription_plan = Column(String(32), default="free", nullable=False)  # free | basic | medium | master | gov
    # Papel do usuário: user | teacher | researcher | enterprise
    # is_admin=True continua sendo o flag de administrador do sistema
    role = Column(String(32), default="user", nullable=False)
    # 2FA TOTP (admin / plano gov) — opcional
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False)
    backup_codes_json = Column(Text, nullable=True)  # JSON: lista de hashes bcrypt

    # Subscription / Billing fields
    subscription_status = Column(String(32), default="trial", nullable=False)  # trial | active | overdue | suspended | cancelled | expired
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    renewal_date = Column(DateTime, nullable=True)
    payment_status = Column(String(32), default="pending", nullable=False)  # pending | paid | failed | overdue | refunded
    payment_gateway = Column(String(32), nullable=True)  # stripe | pagarme | pagbank | coinbase
    payment_gateway_customer_id = Column(String(255), nullable=True)
    payment_gateway_subscription_id = Column(String(255), nullable=True)
    last_payment_date = Column(DateTime, nullable=True)
    last_payment_amount = Column(Float, nullable=True)
    payment_failure_count = Column(Integer, default=0)
    usage_limits = Column(JSON, default=dict, nullable=True)  # {"messages": 200, "whatsapp_connections": 1}
    feature_flags = Column(JSON, default=dict, nullable=True)  # {"premium_ai": true, "whatsapp_saas": false}
    billing_email = Column(String(255), nullable=True)
    billing_name = Column(String(255), nullable=True)
    billing_document = Column(String(32), nullable=True)
    grace_period_until = Column(DateTime, nullable=True)  # Período de carência após vencimento

    created_at = Column(DateTime, default=datetime.utcnow)
    chat_sessions = relationship("ChatSession", back_populates="user")


class ChatSession(Base):
    """Sessão de chat: agrupa mensagens por conversa para memória e histórico."""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(512), nullable=True, default="Nova conversa")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    logs = relationship("ConversationLog", back_populates="session", order_by="ConversationLog.created_at")


class Session(Base):
    """
    Sessão v2 (profissional): identificação de canal/dispositivo e idioma padrão.
    Mantém ChatSession legada para compatibilidade retroativa.
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    channel = Column(String(32), nullable=False, default="web")
    source = Column(String(64), nullable=True)
    language = Column(String(16), nullable=True, default="pt-BR")
    is_anonymous = Column(Boolean, nullable=False, default=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")
    conversations = relationship("Conversation", back_populates="session")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(512), nullable=True, default="Nova conversa")
    status = Column(String(32), nullable=False, default="active")
    detected_language = Column(String(16), nullable=True, default="pt-BR")
    detected_subject = Column(String(128), nullable=True)
    detected_sentiment = Column(String(32), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    session = relationship("Session", back_populates="conversations")
    user = relationship("User")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")
    model_runs = relationship("ModelRun", back_populates="conversation", order_by="ModelRun.created_at")


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    tags = Column(String(255), default="")

    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User")


class ConversationLog(Base):
    __tablename__ = "conversation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    role = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    model_used = Column(String(64), nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    detected_language = Column(String(16), nullable=True)
    detected_subject = Column(String(128), nullable=True)
    detected_sentiment = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    session = relationship("ChatSession", back_populates="logs")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    role = Column(String(32), nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    language = Column(String(16), nullable=True, default="pt-BR")
    subject = Column(String(128), nullable=True)
    sentiment = Column(String(32), nullable=True)
    model_used = Column(String(64), nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    if Vector is not None:
        embedding_vector = Column(Vector(EMBEDDING_VECTOR_DIM), nullable=True)
    embedding_json = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User")


class MemoryItem(Base):
    """Memória de longo prazo por usuário (preferências, fatos, contexto)."""
    __tablename__ = "memory_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key = Column(String(255), nullable=False, index=True)
    value = Column(Text, nullable=False)
    language = Column(String(16), nullable=True, default="pt-BR")
    subject = Column(String(128), nullable=True)
    sentiment = Column(String(32), nullable=True)
    source = Column(String(64), nullable=False, default="chat")
    if Vector is not None:
        embedding_vector = Column(Vector(EMBEDDING_VECTOR_DIM), nullable=True)
    embedding_json = Column(JSON, nullable=True)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_memory_items_user_key"),
    )


class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True, index=True)
    provider = Column(String(64), nullable=False)  # ollama | openai | syntexa_future
    model_name = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False, default="success")
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    estimated_cost_usd = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="model_runs")
    message = relationship("Message")


class AutonomyTask(Base):
    """
    Tarefa autônoma: plano -> execução -> verificação.
    Persistida no banco para retomada/observabilidade.
    """

    __tablename__ = "autonomy_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="queued")  # queued|running|succeeded|failed|cancelled
    priority = Column(Integer, nullable=False, default=5)  # 1=alta, 10=baixa
    prompt = Column(Text, nullable=False)
    plan_text = Column(Text, nullable=True)
    steps_json = Column(JSON, nullable=True)
    outputs_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True, index=True)
    score = Column(Integer, nullable=True)  # 1-5, ou -1/1
    category = Column(String(64), nullable=True)  # quality, safety, helpfulness
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
    conversation = relationship("Conversation")
    message = relationship("Message")


class AutoTrainLog(Base):
    """Registro de auto-treino: exemplos gerados a partir de conversas/feedback."""
    __tablename__ = "auto_train_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    input_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=False)
    source = Column(String(64), default="conversation")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    session = relationship("ChatSession")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    conversation_log_id = Column(
        Integer, ForeignKey("conversation_logs.id"), nullable=False
    )
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User")


class AuditLog(Base):
    """Log de auditoria para controle de acesso e conformidade LGPD."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resource = Column(String(255), nullable=True)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class InstitutionalClient(Base):
    """
    Cliente institucional (escola, município, secretaria, universidade).
    Cada registro representa uma contratação/licença do sistema offline.
    """
    __tablename__ = "institutional_clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)                  # Ex: "Escola Estadual João XXIII"
    cnpj = Column(String(20), nullable=True, index=True)        # CNPJ da instituição
    client_type = Column(String(32), nullable=False, default="escola")
    # escola | municipio | estado | universidade | federal
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(32), nullable=True)
    city = Column(String(128), nullable=True)
    state = Column(String(64), nullable=True)
    plan = Column(String(32), nullable=False, default="basico")  # basico | avancado | enterprise
    license_key = Column(String(128), unique=True, nullable=False, index=True)
    active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)  # Heartbeat do sistema instalado


class RefreshToken(Base):
    """Refresh tokens opacos (hash SHA-256 armazenado)."""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class VerificationCode(Base):
    """Códigos de verificação (cadastro e reset de senha)."""
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String(16), nullable=False, index=True)
    purpose = Column(String(32), nullable=False, index=True)  # "signup" | "reset"
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)

    user = relationship("User")


class ApiIntegrationToken(Base):
    """Token de integração para clientes/sistemas externos consumirem a API."""
    __tablename__ = "api_integration_tokens"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    token_prefix = Column(String(24), nullable=False, index=True)
    scopes = Column(String(255), nullable=False, default="chat:read,chat:write")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)

    owner = relationship("User")
