from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    default_llm: str = Field(default="dummy", validation_alias="DEFAULT_LLM")
    local_llm_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_LLM_ENDPOINT"
    )
    ollama_endpoint: str | None = Field(
        default=None, validation_alias="OLLAMA_ENDPOINT"
    )
    ollama_model: str = Field(default="mistral", validation_alias="OLLAMA_MODEL")
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
        default=4,
        validation_alias="LLM_MAX_CONCURRENCY",
        description="Limite local de chamadas simultâneas ao LLM.",
    )
    llm_soft_timeout: float = Field(
        default=20.0,
        validation_alias="LLM_SOFT_TIMEOUT",
        description="Timeout de UX para resposta rápida (segundos).",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
