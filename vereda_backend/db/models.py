from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from vereda_backend.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    full_name = Column(String(255), nullable=True)
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
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    session = relationship("ChatSession", back_populates="logs")


class MemoryItem(Base):
    """Memória de longo prazo por usuário (preferências, fatos, contexto)."""
    __tablename__ = "memory_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key = Column(String(255), nullable=False, index=True)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


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
