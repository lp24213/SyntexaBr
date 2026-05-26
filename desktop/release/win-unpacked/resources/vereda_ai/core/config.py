from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Raiz do repositório (vereda_ai/core/config.py → parents[2]). Garante OLLAMA_* mesmo se o
# processo arranca com cwd ≠ raiz (Docker, systemd, IDE).
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Lista de origens em string crua (não usada diretamente pelo vereda_ai)
    frontend_origins: str = ""

    # Campos realmente usados pelo vereda_ai
    secret_key: str = Field(default="dev-secret-key", validation_alias="VEREDA_SECRET")
    access_token_exp_hours: int = 12
    database_url: str = Field(
        default="sqlite:///./vereda_ai.db",
        validation_alias="VEREDA_DATABASE_URL",
    )
    default_llm: str = Field(default="syntexa_native", validation_alias="DEFAULT_LLM")
    # Ollama: mesmo processo (local :11434 ou Ollama Cloud) — API compatível OpenAI em /v1/*
    ollama_endpoint: str | None = Field(default=None, validation_alias="OLLAMA_ENDPOINT")
    ollama_model: str | None = Field(default=None, validation_alias="OLLAMA_MODEL")
    ollama_api_key: str | None = Field(
        default=None,
        validation_alias="OLLAMA_API_KEY",
        description="Opcional (Ollama Cloud / proxy). Local em 127.0.0.1 costuma não precisar.",
    )
    local_llm_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_LLM_ENDPOINT"
    )
    # ExLlama (exllamav2) endpoint/local gateway
    exllama_endpoint: str | None = Field(default=None, validation_alias="EXLLAMA_ENDPOINT")
    exllama_model: str | None = Field(default=None, validation_alias="EXLLAMA_MODEL")
    # Azure / Remote LLM (opcional)
    azure_tgi_endpoint: str | None = Field(default=None, validation_alias="AZURE_TGI_ENDPOINT")
    azure_tgi_key: str | None = Field(default=None, validation_alias="AZURE_TGI_KEY")
    azure_tgi_model: str | None = Field(default=None, validation_alias="AZURE_TGI_MODEL")
    azure_openai_endpoint: str | None = Field(default=None, validation_alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: str | None = Field(default=None, validation_alias="AZURE_OPENAI_KEY")
    azure_openai_deployment: str | None = Field(default=None, validation_alias="AZURE_OPENAI_DEPLOYMENT")
    remote_llm_endpoint: str | None = Field(default=None, validation_alias="REMOTE_LLM_ENDPOINT")
    remote_llm_model: str | None = Field(default=None, validation_alias="REMOTE_LLM_MODEL")
    openai_endpoint: str | None = Field(default=None, validation_alias="OPENAI_ENDPOINT")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str | None = Field(default=None, validation_alias="OPENAI_MODEL")
    # DeepSeek (OpenAI-compatible)
    deepseek_endpoint: str | None = Field(default="https://api.deepseek.com", validation_alias="DEEPSEEK_ENDPOINT")
    deepseek_api_key: str | None = Field(default=None, validation_alias="DEEPSEEK_API_KEY")
    deepseek_model: str | None = Field(default=None, validation_alias="DEEPSEEK_MODEL")
    # Google Gemini (OpenAI-compatible endpoint)
    gemini_endpoint: str | None = Field(default="https://generativelanguage.googleapis.com/v1beta/openai", validation_alias="GEMINI_ENDPOINT")
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_model: str | None = Field(default=None, validation_alias="GEMINI_MODEL")
    # Anthropic Claude (Messages API)
    anthropic_endpoint: str | None = Field(default="https://api.anthropic.com", validation_alias="ANTHROPIC_ENDPOINT")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    anthropic_model: str | None = Field(default=None, validation_alias="ANTHROPIC_MODEL")
    # vLLM local endpoint (OpenAI-compatible)
    vllm_endpoint: str | None = Field(default=None, validation_alias="VLLM_ENDPOINT")
    vllm_model: str | None = Field(default=None, validation_alias="VLLM_MODEL")
    # Runtime local soberano
    local_runtime_enabled: bool = Field(default=True, validation_alias="LOCAL_RUNTIME_ENABLED")
    external_providers_enabled: bool = Field(default=False, validation_alias="EXTERNAL_PROVIDERS_ENABLED")
    runtime_backend: str = Field(default="auto", validation_alias="RUNTIME_BACKEND")
    local_model_path: str | None = Field(default=None, validation_alias="LOCAL_MODEL_PATH")
    quantization_mode: str | None = Field(default=None, validation_alias="QUANTIZATION_MODE")
    gpu_memory_utilization: float = Field(default=0.9, validation_alias="GPU_MEMORY_UTILIZATION")
    tensor_parallel_size: int = Field(default=1, validation_alias="TENSOR_PARALLEL_SIZE")
    llm_chat_timeout: int = Field(
        default=120,
        validation_alias="LLM_CHAT_TIMEOUT",
        description="Timeout em segundos para chamadas ao LLM.",
    )
    llm_connect_timeout: float = Field(
        default=3.0,
        validation_alias="LLM_CONNECT_TIMEOUT",
        description="Timeout de conexão HTTP ao LLM (segundos).",
    )
    llm_read_timeout: float = Field(
        default=120.0,
        validation_alias="LLM_READ_TIMEOUT",
        description="Timeout de leitura HTTP ao LLM (segundos).",
    )
    llm_stream_read_timeout: float = Field(
        default=900.0,
        validation_alias="LLM_STREAM_READ_TIMEOUT",
        description="Timeout de leitura para respostas SSE em streaming (segundos).",
    )
    llm_retry_count: int = Field(
        default=3,
        validation_alias="LLM_RETRY_COUNT",
        description="Quantidade total de tentativas em erro transitório.",
    )
    llm_retry_backoff_ms: int = Field(
        default=150,
        validation_alias="LLM_RETRY_BACKOFF_MS",
        description="Backoff base entre tentativas (ms).",
    )
    llm_max_concurrency: int = Field(
        default=32,
        validation_alias="LLM_MAX_CONCURRENCY",
        description="Limite local de chamadas simultâneas ao LLM.",
    )
    llm_soft_timeout: float = Field(
        default=300.0,
        validation_alias="LLM_SOFT_TIMEOUT",
        description="Timeout de UX para resposta completa sem cortar cedo (segundos).",
    )
    llm_smart_fallback_enabled: bool = Field(
        default=True,
        validation_alias="LLM_SMART_FALLBACK_ENABLED",
        description="Ativa fallback ordenado por confiança/qualidade entre provedores registrados.",
    )
    llm_smart_fallback_min_confidence: float = Field(
        default=0.55,
        validation_alias="LLM_SMART_FALLBACK_MIN_CONFIDENCE",
        description="Piso de confiança do provedor para ser elegível no fallback inteligente.",
    )
    llm_quality_scoreboard_path: str = Field(
        default="config/llm_quality_scoreboard.json",
        validation_alias="LLM_QUALITY_SCOREBOARD_PATH",
        description="Caminho do placar de qualidade por provedor/domínio.",
    )
    llm_domain_provider_overrides: str = Field(
        default="",
        validation_alias="LLM_DOMAIN_PROVIDER_OVERRIDES",
        description="Overrides de domínio em formato domain=provider,domain=provider.",
    )
    own_model_max_new_tokens: int = Field(
        default=1024,
        validation_alias="OWN_MODEL_MAX_NEW_TOKENS",
        description="Quantidade máxima de novos tokens na geração da IA proprietária.",
    )
    own_model_temperature: float = Field(
        default=0.8,
        validation_alias="OWN_MODEL_TEMPERATURE",
        description="Temperatura de geração da IA proprietária.",
    )
    own_model_top_k: int = Field(
        default=80,
        validation_alias="OWN_MODEL_TOP_K",
        description="Top-k sampling da IA proprietária.",
    )
    own_model_strict_no_fallback: bool = Field(
        default=False,
        validation_alias="OWN_MODEL_STRICT_NO_FALLBACK",
        description="Quando ativo, a IA própria não cai para respostas heurísticas/fallback.",
    )
    own_model_sovereign_mode: bool = Field(
        default=True,
        validation_alias="OWN_MODEL_SOVEREIGN_MODE",
        description="Quando ativo, bloqueia provedores externos e mantém apenas runtime Syntexa próprio.",
    )
    prefer_external_llm_when_configured: bool = Field(
        default=False,
        validation_alias="PREFER_EXTERNAL_LLM_WHEN_CONFIGURED",
        description="Quando true (dev/test), permite trocar syntexa_native automaticamente por um endpoint HTTP/ollama configurado.",
    )
    environment: str = Field(
        default="local",
        validation_alias="ENVIRONMENT",
        description="Alinhado com backend: production ativa validações estritas no motor legado.",
    )
    # Embeddings open-source (RAG, memória, pgvector JSON): auto = Ollama → FastEmbed → HTTP → hash
    embedding_backend: str = Field(
        default="auto",
        validation_alias="EMBEDDING_BACKEND",
        description="native | auto | ollama | fastembed | openai_http",
    )
    ollama_embed_model: str | None = Field(
        default="nomic-embed-text",
        validation_alias="OLLAMA_EMBED_MODEL",
        description="Modelo Ollama para POST /api/embed (ex.: nomic-embed-text, mxbai-embed-large).",
    )
    embedding_http_endpoint: str | None = Field(
        default=None,
        validation_alias="EMBEDDING_HTTP_ENDPOINT",
        description="Base URL para /v1/embeddings (vLLM, LiteLLM, etc.); se vazio, usa LOCAL_LLM em modo auto.",
    )
    embedding_openai_model: str | None = Field(
        default="text-embedding-3-small",
        validation_alias="EMBEDDING_OPENAI_MODEL",
        description="Nome do modelo no endpoint de embeddings OpenAI-compatible.",
    )
    fastembed_model_name: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        validation_alias="FASTEMBED_MODEL_NAME",
        description="Modelo FastEmbed (ONNX, Apache-2.0) — bom para PT/EN sem GPU.",
    )
    model_config = SettingsConfigDict(
        env_file=(str(_REPO_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("default_llm", mode="before")
    @classmethod
    def _default_llm_normalize(cls, v: object) -> str:
        s = str(v or "").strip().lower()
        return s or "syntexa_native"


settings = Settings()
