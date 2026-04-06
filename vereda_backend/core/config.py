from typing import List

from pydantic import EmailStr, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_frontend_origins(v: object) -> List[str]:
    """Parse FRONTEND_ORIGIN do .env: tolera valores inválidos, ignora '...://', retorna lista."""
    if v is None or v == "":
        return ["*"]
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    s = str(v).replace("...", "").strip()
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return parts if parts else ["*"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    project_name: str = "Syntexa AI"
    api_v1_prefix: str = "/v1"
    environment: str = Field(default="local", validation_alias="ENVIRONMENT")

    # String no .env (ex.: https://a.com,https://b.com). List[str] direto quebra o parser
    # do pydantic-settings, que tenta JSON antes do validator.
    frontend_origin_raw: str = Field(
        default="*",
        validation_alias="FRONTEND_ORIGIN",
    )

    secret_key: str = Field(
        default="dev-secret-key-change-me", validation_alias="VEREDA_SECRET_KEY"
    )
    admin_email: str = Field(
        default="admin@syntexa.dev", validation_alias="VEREDA_ADMIN_EMAIL"
    )
    admin_password: str = Field(
        default="admin123", validation_alias="VEREDA_ADMIN_PASSWORD"
    )
    resend_api_key: str | None = Field(
        default=None, validation_alias="RESEND_API_KEY"
    )
    brevo_api_key: str | None = Field(
        default=None, validation_alias="BREVO_API_KEY"
    )
    resend_from_email: str | None = Field(
        default=None, validation_alias="RESEND_FROM_EMAIL"
    )
    resend_to_email: EmailStr | None = Field(
        default=None, validation_alias="RESEND_TO_EMAIL"
    )
    stripe_secret_key: str = Field(default="", validation_alias="STRIPE_SECRET_KEY")
    stripe_price_basic: str = Field(default="", validation_alias="STRIPE_PRICE_BASIC")
    stripe_price_medium: str = Field(default="", validation_alias="STRIPE_PRICE_MEDIUM")
    stripe_price_master: str = Field(default="", validation_alias="STRIPE_PRICE_MASTER")
    stripe_webhook_secret: str = Field(default="", validation_alias="STRIPE_WEBHOOK_SECRET")
    frontend_base_url: str = Field(
        default="https://syntexabr.com.br", validation_alias="FRONTEND_BASE_URL"
    )
    default_llm: str = "dummy"
    local_llm_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_LLM_ENDPOINT"
    )
    # Serviços locais/open-source (sem chave externa)
    ollama_endpoint: str | None = Field(
        default=None, validation_alias="OLLAMA_ENDPOINT"
    )
    ollama_model: str = Field(
        default="llama3.2:1b", validation_alias="OLLAMA_MODEL"
    )
    ollama_vision_model: str = Field(
        default="llava:7b", validation_alias="OLLAMA_VISION_MODEL"
    )
    local_image_gen_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_IMAGE_GEN_ENDPOINT"
    )
    local_video_gen_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_VIDEO_GEN_ENDPOINT"
    )
    local_music_gen_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_MUSIC_GEN_ENDPOINT"
    )
    local_stt_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_STT_ENDPOINT"
    )
    local_tts_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_TTS_ENDPOINT"
    )
    # Replicate (imagem/vídeo/música de verdade — precisa REPLICATE_API_TOKEN em produção)
    replicate_api_token: str | None = Field(
        default=None, validation_alias="REPLICATE_API_TOKEN"
    )
    replicate_image_model: str = Field(
        default="black-forest-labs/flux-schnell",
        validation_alias="REPLICATE_IMAGE_MODEL",
    )
    replicate_video_model: str = Field(
        default="prunaai/p-video",
        validation_alias="REPLICATE_VIDEO_MODEL",
    )
    # Opcional: URL de imagem inicial para prunaai/p-video (senão gera com REPLICATE_IMAGE_MODEL)
    replicate_video_seed_image_url: str | None = Field(
        default=None, validation_alias="REPLICATE_VIDEO_SEED_IMAGE_URL"
    )
    replicate_pvideo_duration: int = Field(
        default=5, validation_alias="REPLICATE_PVIDEO_DURATION"
    )
    replicate_pvideo_resolution: str = Field(
        default="720p", validation_alias="REPLICATE_PVIDEO_RESOLUTION"
    )
    replicate_music_model: str = Field(
        default="meta/musicgen-small",
        validation_alias="REPLICATE_MUSIC_MODEL",
    )
    edge_tts_voice: str = Field(
        default="pt-BR-FranciscaNeural",
        validation_alias="EDGE_TTS_VOICE",
    )
    chat_cache_ttl_sec: int = Field(
        default=45, validation_alias="CHAT_CACHE_TTL_SEC"
    )
    chat_singleflight_wait_sec: float = Field(
        default=8.0, validation_alias="CHAT_SINGLEFLIGHT_WAIT_SEC"
    )
    # Redis: filas ARQ + cache (opcional — sem REDIS_URL o sistema segue 100% in-process)
    redis_url: str | None = Field(default=None, validation_alias="REDIS_URL")
    # TTL cache Redis para respostas de chat (segundos)
    redis_chat_cache_ttl_sec: int = Field(default=120, validation_alias="REDIS_CHAT_CACHE_TTL_SEC")
    # A partir deste max_tokens, a conclusão de chat pode ir para worker ARQ (se Redis ativo)
    chat_long_job_threshold_tokens: int = Field(
        default=2500, validation_alias="CHAT_LONG_JOB_THRESHOLD_TOKENS"
    )
    refresh_token_expire_days: int = Field(default=30, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS")
    access_token_expire_minutes: int = Field(default=720, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    # Produção atrás do Worker Cloudflare: rejeita requisições sem CF-Connecting-IP (dev/local = False)
    require_cloudflare: bool = Field(default=False, validation_alias="REQUIRE_CLOUDFLARE")

    # Fase 2 — orçamento de contexto / saída (menos tokens = mais throughput no mesmo CPU)
    chat_max_messages: int = Field(default=12, validation_alias="CHAT_MAX_MESSAGES")
    chat_max_message_chars: int = Field(default=6000, validation_alias="CHAT_MAX_MESSAGE_CHARS")
    chat_max_output_tokens_default: int = Field(
        default=768, validation_alias="CHAT_MAX_OUTPUT_TOKENS_DEFAULT"
    )
    chat_max_output_tokens_long: int = Field(
        default=3072, validation_alias="CHAT_MAX_OUTPUT_TOKENS_LONG"
    )
    chat_memory_top_k: int = Field(default=1, validation_alias="CHAT_MEMORY_TOP_K")
    chat_rag_top_k: int = Field(default=1, validation_alias="CHAT_RAG_TOP_K")
    chat_shared_cache_ttl_sec: int = Field(default=300, validation_alias="CHAT_SHARED_CACHE_TTL_SEC")

    # Fase 3 — estabilidade sob pico (sem infra nova)
    global_max_concurrent_llm: int = Field(default=12, validation_alias="GLOBAL_MAX_CONCURRENT_LLM")
    per_user_max_concurrent_llm: int = Field(default=3, validation_alias="PER_USER_MAX_CONCURRENT_LLM")
    slot_timeout_gov_sec: float = Field(default=300.0, validation_alias="SLOT_TIMEOUT_GOV_SEC")
    slot_timeout_auth_sec: float = Field(default=120.0, validation_alias="SLOT_TIMEOUT_AUTH_SEC")
    slot_timeout_public_sec: float = Field(default=45.0, validation_alias="SLOT_TIMEOUT_PUBLIC_SEC")
    load_stress_weight_cpu: float = Field(default=0.55, validation_alias="LOAD_STRESS_WEIGHT_CPU")
    load_stress_weight_mem: float = Field(default=0.45, validation_alias="LOAD_STRESS_WEIGHT_MEM")
    load_degrade_scale_min: float = Field(default=0.52, validation_alias="LOAD_DEGRADE_SCALE_MIN")
    load_queue_stress_threshold: float = Field(default=0.78, validation_alias="LOAD_QUEUE_STRESS_THRESHOLD")
    load_gov_boost_scale: float = Field(default=0.12, validation_alias="LOAD_GOV_BOOST_SCALE")
    session_create_per_ip_hour: int = Field(default=40, validation_alias="SESSION_CREATE_PER_IP_HOUR")

    @computed_field
    @property
    def frontend_origins(self) -> List[str]:
        return _parse_frontend_origins(self.frontend_origin_raw)


settings = Settings()


def _validate_production_settings(s: Settings) -> None:
    env = (s.environment or "").strip().lower()
    is_prod = env in {"prod", "production"}
    if not is_prod:
        return

    insecure_secret_values = {"", "dev-secret-key-change-me", "dev-secret-key"}
    if (s.secret_key or "").strip() in insecure_secret_values or len((s.secret_key or "").strip()) < 32:
        raise ValueError(
            "VEREDA_SECRET_KEY insegura para produção. "
            "Defina uma chave forte (>=32 chars) no .env."
        )

    insecure_admin_pw = {"", "admin123", "password", "123456"}
    if (s.admin_password or "").strip() in insecure_admin_pw or len((s.admin_password or "").strip()) < 10:
        raise ValueError(
            "VEREDA_ADMIN_PASSWORD insegura para produção. "
            "Defina senha forte no .env."
        )


_validate_production_settings(settings)
