from pathlib import Path
from typing import List

from pydantic import EmailStr, Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


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
        env_file=(str(_REPO_ROOT / ".env"), ".env"),
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
    ops_alert_email: EmailStr | None = Field(
        default=None, validation_alias="OPS_ALERT_EMAIL"
    )
    stripe_secret_key: str = Field(default="", validation_alias="STRIPE_SECRET_KEY")
    stripe_price_basic: str = Field(default="", validation_alias="STRIPE_PRICE_BASIC")
    stripe_price_medium: str = Field(default="", validation_alias="STRIPE_PRICE_MEDIUM")
    stripe_price_master: str = Field(default="", validation_alias="STRIPE_PRICE_MASTER")
    stripe_webhook_secret: str = Field(default="", validation_alias="STRIPE_WEBHOOK_SECRET")
    turnstile_secret_key: str | None = Field(
        default=None, validation_alias="TURNSTILE_SECRET_KEY",
        description="Chave secreta Cloudflare Turnstile (siteverify).",
    )
    frontend_base_url: str = Field(
        default="https://syntexabr.com.br", validation_alias="FRONTEND_BASE_URL"
    )
    # URL pública da API (redirects de download /v1/desktop/binary).
    api_public_base_url: str = Field(
        default="https://api.syntexabr.com.br", validation_alias="API_PUBLIC_BASE_URL"
    )
    github_client_id: str | None = Field(
        default=None, validation_alias="GITHUB_CLIENT_ID"
    )
    github_client_secret: str | None = Field(
        default=None, validation_alias="GITHUB_CLIENT_SECRET"
    )
    github_oauth_callback_url: str | None = Field(
        default=None, validation_alias="GITHUB_OAUTH_CALLBACK_URL"
    )
    # Caminho da página de login após OAuth (ex.: /B_4mhVUCNloA se o site usa rotas ofuscadas).
    frontend_oauth_return_path: str = Field(
        default="/login", validation_alias="FRONTEND_OAUTH_RETURN_PATH"
    )
    # Página pública de downloads (rota ofuscada no site estático).
    frontend_download_path: str = Field(
        default="/D5rZw7mQx2Lc", validation_alias="FRONTEND_DOWNLOAD_PATH"
    )
    # URLs finais dos instaladores (HTTP 302 a partir de GET /v1/desktop/assets/<ficheiro>).
    desktop_windows_url: str = Field(default="", validation_alias="DESKTOP_WINDOWS_URL")
    desktop_macos_url: str = Field(default="", validation_alias="DESKTOP_MACOS_URL")
    desktop_linux_url: str = Field(default="", validation_alias="DESKTOP_LINUX_URL")
    desktop_ubuntu_url: str = Field(default="", validation_alias="DESKTOP_UBUNTU_URL")
    desktop_android_url: str = Field(default="", validation_alias="DESKTOP_ANDROID_URL")
    desktop_android_aab_url: str = Field(default="", validation_alias="DESKTOP_ANDROID_AAB_URL")
    # ── Motor LLM Principal ──────────────────────────────────────
    # DEFAULT_LLM="syntexa_native" = motor proprietário (sem APIs externas)
    default_llm: str = Field(default="syntexa_native", validation_alias="DEFAULT_LLM")

    # Modo soberano: quando True, NUNCA usa providers externos (OpenAI, Claude, etc.)
    own_model_sovereign_mode: bool = Field(
        default=True, validation_alias="OWN_MODEL_SOVEREIGN_MODE"
    )
    # Para usar providers externos, defina explicitamente:
    # OWN_MODEL_SOVEREIGN_MODE=false e EXTERNAL_PROVIDERS_ENABLED=true
    external_providers_enabled: bool = Field(
        default=False, validation_alias="EXTERNAL_PROVIDERS_ENABLED"
    )

    ollama_endpoint: str | None = Field(default=None, validation_alias="OLLAMA_ENDPOINT")
    ollama_model: str | None = Field(default=None, validation_alias="OLLAMA_MODEL")
    ollama_api_key: str | None = Field(default=None, validation_alias="OLLAMA_API_KEY")
    local_llm_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_LLM_ENDPOINT"
    )
    # Modelo no endpoint HTTP de texto (OpenAI-compatible / TGI / gateway próprio)
    local_http_llm_model: str = Field(
        default="local", validation_alias="LOCAL_HTTP_LLM_MODEL"
    )
    # Modelo no endpoint HTTP de visão (opcional; núcleo proprietário não exige isto)
    vision_llm_model: str = Field(
        default="syntexa-vision", validation_alias="VISION_LLM_MODEL"
    )
    # Azure / Remote LLM endpoints
    azure_tgi_endpoint: str | None = Field(
        default=None, validation_alias="AZURE_TGI_ENDPOINT"
    )
    azure_tgi_key: str | None = Field(
        default=None, validation_alias="AZURE_TGI_KEY"
    )
    azure_tgi_model: str | None = Field(
        default=None, validation_alias="AZURE_TGI_MODEL"
    )
    azure_openai_endpoint: str | None = Field(
        default=None, validation_alias="AZURE_OPENAI_ENDPOINT"
    )
    azure_openai_key: str | None = Field(
        default=None, validation_alias="AZURE_OPENAI_KEY"
    )
    azure_openai_deployment: str | None = Field(
        default=None, validation_alias="AZURE_OPENAI_DEPLOYMENT"
    )
    remote_llm_endpoint: str | None = Field(
        default=None, validation_alias="REMOTE_LLM_ENDPOINT"
    )
    remote_llm_model: str | None = Field(
        default=None, validation_alias="REMOTE_LLM_MODEL"
    )
    openai_endpoint: str | None = Field(default=None, validation_alias="OPENAI_ENDPOINT")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str | None = Field(default=None, validation_alias="OPENAI_MODEL")

    # ── Split Architecture: Gateway Mode & AI Workers ─────────────────
    gateway_mode: bool = Field(
        default=False, validation_alias="GATEWAY_MODE",
        description="Se True, NÃO carrega IA pesada no startup (modo Railway leve).",
    )
    ai_worker_url: str | None = Field(
        default=None, validation_alias="AI_WORKER_URL",
        description="URL do AI Worker (Kaggle/GPU externo).",
    )
    ai_worker_api_key: str | None = Field(
        default=None, validation_alias="AI_WORKER_API_KEY",
    )
    local_ai_url: str | None = Field(
        default=None, validation_alias="LOCAL_AI_URL",
        description="URL do servidor local privado (Ollama).",
    )
    local_ai_api_key: str | None = Field(
        default=None, validation_alias="LOCAL_AI_API_KEY",
    )

    # ── Hybrid Architecture: AWS GPU + Local Fallback ───────────────────
    aws_base_url: str | None = Field(
        default=None, validation_alias="AWS_BASE_URL",
        description="URL do cluster GPU na AWS (vLLM / TGI).",
    )
    local_base_url: str | None = Field(
        default=None, validation_alias="LOCAL_BASE_URL",
        description="URL da infra local híbrida (Ollama / llama.cpp fallback).",
    )
    ai_router_timeout_sec: float = Field(
        default=120.0, validation_alias="AI_ROUTER_TIMEOUT_SEC",
    )
    ai_router_fallback_enabled: bool = Field(
        default=True, validation_alias="AI_ROUTER_FALLBACK_ENABLED",
    )

    # ExLlama (exllamav2) endpoint — servidor HTTP que expõe exllama
    exllama_endpoint: str | None = Field(
        default=None, validation_alias="EXLLAMA_ENDPOINT"
    )
    exllama_model: str | None = Field(
        default=None, validation_alias="EXLLAMA_MODEL"
    )
    local_image_gen_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_IMAGE_GEN_ENDPOINT"
    )
    bfl_api_key: str | None = Field(
        default=None, validation_alias="BFL_API_KEY"
    )
    bfl_api_url: str = Field(
        default="https://api.us1.bfl.ai/v1/{model}",
        validation_alias="BFL_API_URL",
    )
    bfl_model: str = Field(
        default="flux-pro-1.1",
        validation_alias="BFL_MODEL",
    )
    bfl_timeout_sec: int = Field(
        default=90,
        validation_alias="BFL_TIMEOUT_SEC",
    )
    local_video_gen_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_VIDEO_GEN_ENDPOINT"
    )
    media_realism_enhance_prompts: bool = Field(
        default=True,
        validation_alias="MEDIA_REALISM_ENHANCE_PROMPTS",
        description="Enriquece prompts de imagem/vídeo para resultados mais realistas e menos cartoon.",
    )
    media_image_target_resolution: str = Field(
        default="2048x2048",
        validation_alias="MEDIA_IMAGE_TARGET_RESOLUTION",
        description="Resolução alvo de imagem em formato WxH (ex.: 2048x2048).",
    )
    media_image_quality: str = Field(
        default="ultra",
        validation_alias="MEDIA_IMAGE_QUALITY",
        description="Qualidade alvo de imagem enviada a provedores locais.",
    )
    media_image_negative_prompt: str = Field(
        default="lowres, blurry, watermark, artifacts, cartoonish, toy-like geometry, flat icon style",
        validation_alias="MEDIA_IMAGE_NEGATIVE_PROMPT",
    )
    media_video_target_resolution: str = Field(
        default="1920x1080",
        validation_alias="MEDIA_VIDEO_TARGET_RESOLUTION",
        description="Resolução alvo de vídeo (ex.: 1920x1080).",
    )
    media_video_target_fps: int = Field(
        default=30,
        validation_alias="MEDIA_VIDEO_TARGET_FPS",
    )
    media_video_target_duration_sec: int = Field(
        default=8,
        validation_alias="MEDIA_VIDEO_TARGET_DURATION_SEC",
    )
    media_video_quality: str = Field(
        default="cinematic",
        validation_alias="MEDIA_VIDEO_QUALITY",
    )
    media_video_negative_prompt: str = Field(
        default="blurry, jitter, flicker, low-detail, unrealistic anatomy, flat geometric-only scenes",
        validation_alias="MEDIA_VIDEO_NEGATIVE_PROMPT",
    )
    media_generation_cache_enabled: bool = Field(
        default=True,
        validation_alias="MEDIA_GENERATION_CACHE_ENABLED",
        description="Cache de geração multimídia por prompt (reduz custo sob carga).",
    )
    media_generation_cache_ttl_sec: int = Field(
        default=300,
        validation_alias="MEDIA_GENERATION_CACHE_TTL_SEC",
        description="TTL (segundos) do cache por prompt para imagem/vídeo/música.",
    )
    media_queue_video_enabled: bool = Field(
        default=True,
        validation_alias="MEDIA_QUEUE_VIDEO_ENABLED",
        description="Quando Redis/ARQ estiver ativo, enfileira geração de vídeo.",
    )
    media_queue_music_enabled: bool = Field(
        default=True,
        validation_alias="MEDIA_QUEUE_MUSIC_ENABLED",
        description="Quando Redis/ARQ estiver ativo, enfileira geração de música.",
    )
    media_queue_video_timeout_sec: int = Field(
        default=900,
        validation_alias="MEDIA_QUEUE_VIDEO_TIMEOUT_SEC",
    )
    media_queue_music_timeout_sec: int = Field(
        default=900,
        validation_alias="MEDIA_QUEUE_MUSIC_TIMEOUT_SEC",
    )
    # Geração assíncrona (/media/.../generate-async): anti-flood, idempotência e prioridade na fila ARQ
    media_async_rate_limit_enabled: bool = Field(
        default=True,
        validation_alias="MEDIA_ASYNC_RATE_LIMIT_ENABLED",
        description="Ativa limite de pedidos generate-async por IP+utilizador (Redis).",
    )
    media_async_rate_limit_window_sec: int = Field(
        default=60,
        validation_alias="MEDIA_ASYNC_RATE_LIMIT_WINDOW_SEC",
    )
    media_async_rate_limit_anon: int = Field(
        default=24,
        validation_alias="MEDIA_ASYNC_RATE_LIMIT_ANON",
    )
    media_async_rate_limit_free: int = Field(
        default=40,
        validation_alias="MEDIA_ASYNC_RATE_LIMIT_FREE",
    )
    media_async_rate_limit_basic: int = Field(
        default=60,
        validation_alias="MEDIA_ASYNC_RATE_LIMIT_BASIC",
    )
    media_async_rate_limit_paid: int = Field(
        default=120,
        validation_alias="MEDIA_ASYNC_RATE_LIMIT_PAID",
        description="medium + master (e planos não mapeados tratados como paid aqui).",
    )
    media_idempotency_ttl_sec: int = Field(
        default=86400,
        validation_alias="MEDIA_IDEMPOTENCY_TTL_SEC",
        description="TTL Redis para X-Idempotency-Key → job_id.",
    )
    media_job_context_ttl_sec: int = Field(
        default=7200,
        validation_alias="MEDIA_JOB_CONTEXT_TTL_SEC",
        description="Metadados job_id → kind/prompt para cache ao completar (GET /jobs).",
    )
    media_arq_defer_sec_admin: float = Field(
        default=0.0,
        validation_alias="MEDIA_ARQ_DEFER_SEC_ADMIN",
    )
    media_arq_defer_sec_paid: float = Field(
        default=0.12,
        validation_alias="MEDIA_ARQ_DEFER_SEC_PAID",
    )
    media_arq_defer_sec_basic: float = Field(
        default=0.55,
        validation_alias="MEDIA_ARQ_DEFER_SEC_BASIC",
    )
    media_arq_defer_sec_free: float = Field(
        default=1.0,
        validation_alias="MEDIA_ARQ_DEFER_SEC_FREE",
    )
    media_arq_defer_sec_anon: float = Field(
        default=1.6,
        validation_alias="MEDIA_ARQ_DEFER_SEC_ANON",
    )
    local_music_gen_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_MUSIC_GEN_ENDPOINT"
    )
    local_stt_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_STT_ENDPOINT"
    )
    # Azure AI Speech (STT) — https://portal.azure.com → recurso Speech
    azure_speech_key: str | None = Field(default=None, validation_alias="AZURE_SPEECH_KEY")
    azure_speech_region: str | None = Field(
        default=None,
        validation_alias="AZURE_SPEECH_REGION",
        description="Ex.: brazilsouth, eastus",
    )
    azure_tts_voice: str = Field(
        default="pt-BR-FranciscaNeural",
        validation_alias="AZURE_TTS_VOICE",
        description="Voz neural Azure Speech (TTS); ex.: pt-BR-FranciscaNeural",
    )
    local_tts_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_TTS_ENDPOINT"
    )
    edge_tts_voice: str = Field(
        default="pt-BR-FranciscaNeural",
        validation_alias="EDGE_TTS_VOICE",
    )
    # Modo estrito (produção): sem fallbacks sintéticos/gratuitos.
    # - Quando true: mídia exige endpoints locais no VPS ou política explícita.
    # - Pollinations e placeholders (GIF/WAV) são desativados salvo MEDIA_USE_POLLINATIONS.
    media_strict_real_providers: bool = Field(
        default=True, validation_alias="MEDIA_STRICT_REAL_PROVIDERS"
    )
    media_use_pollinations: bool = Field(
        default=True,
        validation_alias="MEDIA_USE_POLLINATIONS",
        description="Fallback servidor (Pollinations) quando não há LOCAL_IMAGE_GEN — evita login Puter no browser.",
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
    chat_max_messages: int = Field(default=48, validation_alias="CHAT_MAX_MESSAGES")
    chat_max_message_chars: int = Field(default=12000, validation_alias="CHAT_MAX_MESSAGE_CHARS")
    chat_max_output_tokens_default: int = Field(
        default=4096, validation_alias="CHAT_MAX_OUTPUT_TOKENS_DEFAULT"
    )
    chat_max_output_tokens_long: int = Field(
        default=8192, validation_alias="CHAT_MAX_OUTPUT_TOKENS_LONG"
    )
    # Teto absoluto enviado ao provedor LLM (evita hardcode baixo no motor de chat).
    chat_max_model_tokens: int = Field(
        default=8192, validation_alias="CHAT_MAX_MODEL_TOKENS"
    )
    # Admin: teto maior (respeita limite real do modelo/engine configurado).
    chat_max_output_tokens_admin: int = Field(
        default=16384,
        validation_alias="CHAT_MAX_OUTPUT_TOKENS_ADMIN",
        description="Teto de max_tokens para admin (sem corte artificial em respostas longas).",
    )
    chat_max_model_tokens_admin: int = Field(
        default=16384,
        validation_alias="CHAT_MAX_MODEL_TOKENS_ADMIN",
        description="Teto enviado ao provedor quando user é admin (limitado pelo modelo).",
    )
    # Pedidos «profundos» (ver `vereda_backend.core.deep_run`): teto extra de saída/contexto (0 = não usar).
    chat_deep_run_max_output_tokens: int = Field(
        default=12288,
        validation_alias="CHAT_DEEP_RUN_MAX_OUTPUT_TOKENS",
        description="Teto de max_tokens no prepare quando deep_run; deve caber no modelo.",
    )
    chat_deep_run_max_model_tokens: int = Field(
        default=12288,
        validation_alias="CHAT_DEEP_RUN_MAX_MODEL_TOKENS",
        description="Teto enviado ao provedor em deep_run (minimo do pedido e deste valor).",
    )
    chat_deep_run_min_output_tokens: int = Field(
        default=4096,
        validation_alias="CHAT_DEEP_RUN_MIN_OUTPUT_TOKENS",
        description="Piso de max_tokens em deep_run após prepare (0 = desligado).",
    )
    chat_deep_run_context_extra_tokens: int = Field(
        default=4000,
        validation_alias="CHAT_DEEP_RUN_CONTEXT_EXTRA_TOKENS",
        description="Soma ao orçamento de contexto aproximado só em deep_run (0 = sem extra).",
    )
    chat_deep_run_knowledge_limit: int = Field(
        default=3,
        validation_alias="CHAT_DEEP_RUN_KNOWLEDGE_LIMIT",
        description="Máx. itens da KB injetados em deep_run (1–8).",
    )
    chat_deep_run_memory_top_k_extra: int = Field(
        default=1,
        validation_alias="CHAT_DEEP_RUN_MEMORY_TOP_K_EXTRA",
        description="Soma a CHAT_MEMORY_TOP_K só em deep_run.",
    )
    chat_deep_run_rag_top_k_extra: int = Field(
        default=2,
        validation_alias="CHAT_DEEP_RUN_RAG_TOP_K_EXTRA",
        description="Soma a CHAT_RAG_TOP_K só em deep_run.",
    )
    chat_deep_run_web_max_extra: int = Field(
        default=6,
        validation_alias="CHAT_DEEP_RUN_WEB_MAX_EXTRA",
        description="Soma aos web_max (definição/geral) em deep_run; limitado no código.",
    )
    chat_deep_run_semantic_top_k_extra: int = Field(
        default=2,
        validation_alias="CHAT_DEEP_RUN_SEMANTIC_TOP_K_EXTRA",
        description="Soma ao top_k de contexto semântico do utilizador em deep_run.",
    )
    chat_deep_run_web_timeout_extra_sec: float = Field(
        default=12.0,
        validation_alias="CHAT_DEEP_RUN_WEB_TIMEOUT_EXTRA_SEC",
        description="Soma ao timeout de busca web só em deep_run (0 = sem extra).",
    )
    chat_deep_run_message_chars_extra: int = Field(
        default=4000,
        validation_alias="CHAT_DEEP_RUN_MESSAGE_CHARS_EXTRA",
        description="Soma a CHAT_MAX_MESSAGE_CHARS (após stress) só em deep_run; 0 = off.",
    )
    # Tectos da agregação web (`answer_engine.build_augmented_web_context`); antes max_results era clampado a 8.
    chat_web_augment_max_results_cap: int = Field(
        default=28,
        validation_alias="CHAT_WEB_AUGMENT_MAX_RESULTS_CAP",
        description="Máximo de resultados híbridos por pergunta (fast e full respeitam até aqui).",
    )
    chat_web_fast_max_total: int = Field(
        default=6,
        validation_alias="CHAT_WEB_FAST_MAX_TOTAL",
        description="Teto do modo rápido quando max_results pedido é baixo (chat normal).",
    )
    chat_web_fast_max_total_deep: int = Field(
        default=16,
        validation_alias="CHAT_WEB_FAST_MAX_TOTAL_DEEP",
        description="Teto do modo rápido quando max_results pedido indica deep (ex. ≥14).",
    )
    chat_web_augment_text_chars: int = Field(
        default=12000,
        validation_alias="CHAT_WEB_AUGMENT_TEXT_CHARS",
        description="Caracteres máx. do texto agregado (modo normal).",
    )
    chat_web_augment_text_chars_deep: int = Field(
        default=22000,
        validation_alias="CHAT_WEB_AUGMENT_TEXT_CHARS_DEEP",
        description="Caracteres máx. do texto agregado quando max_results indica deep.",
    )
    chat_frontier_prompt_enabled: bool = Field(
        default=True,
        validation_alias="CHAT_FRONTIER_PROMPT_ENABLED",
        description="Injeta bloco «contrato de resposta» de alta qualidade no system prompt.",
    )
    chat_deep_run_temperature_adjust_enabled: bool = Field(
        default=True,
        validation_alias="CHAT_DEEP_RUN_TEMPERATURE_ADJUST_ENABLED",
        description="Em deep_run, limita temperatura ao teto abaixo (mais factível em respostas longas).",
    )
    chat_deep_run_temperature_cap: float = Field(
        default=0.62,
        validation_alias="CHAT_DEEP_RUN_TEMPERATURE_CAP",
        description="Máximo de temperature enviado ao LLM quando deep_run (min com o pedido do cliente).",
    )
    chat_auto_domain_modes_enabled: bool = Field(
        default=True,
        validation_alias="CHAT_AUTO_DOMAIN_MODES_ENABLED",
        description="Ativa inferência automática de modo (copiloto/cientifico/juridico/estrategico) por domínio do pedido.",
    )
    # Legado: respostas sintéticas quando o LLM falhava foram removidas; falhas propagam erro real.
    chat_strict_real_providers: bool = Field(
        default=True, validation_alias="CHAT_STRICT_REAL_PROVIDERS"
    )
    chat_memory_top_k: int = Field(default=1, validation_alias="CHAT_MEMORY_TOP_K")
    chat_rag_top_k: int = Field(default=1, validation_alias="CHAT_RAG_TOP_K")
    chat_shared_cache_ttl_sec: int = Field(default=300, validation_alias="CHAT_SHARED_CACHE_TTL_SEC")
    # Janela de contexto aproximada (tokens ~ chars/CHAT_APPROX_CHARS_PER_TOKEN) por tier.
    chat_approx_chars_per_token: float = Field(
        default=4.0,
        validation_alias="CHAT_APPROX_CHARS_PER_TOKEN",
    )
    chat_context_approx_tokens_public: int = Field(
        default=8000,
        validation_alias="CHAT_CONTEXT_APPROX_TOKENS_PUBLIC",
    )
    chat_context_approx_tokens_auth: int = Field(
        default=14000,
        validation_alias="CHAT_CONTEXT_APPROX_TOKENS_AUTH",
    )
    chat_context_approx_tokens_admin: int = Field(
        default=22000,
        validation_alias="CHAT_CONTEXT_APPROX_TOKENS_ADMIN",
    )
    chat_max_messages_admin_floor: int = Field(
        default=36,
        validation_alias="CHAT_MAX_MESSAGES_ADMIN_FLOOR",
        description="Mínimo de mensagens no slice após stress quando o utilizador é admin.",
    )
    # Tempo máximo para agregar fontes (DDG/Wikipedia/etc.) antes de sintetizar no núcleo Syntexa.
    chat_web_search_timeout_sec: float = Field(
        default=22.0,
        validation_alias="CHAT_WEB_SEARCH_TIMEOUT_SEC",
    )
    chat_runtime_alert_cooldown_sec: float = Field(
        default=120.0,
        validation_alias="CHAT_RUNTIME_ALERT_COOLDOWN_SEC",
    )
    # Política de sistema do chat (JSON versionado; hash em runtime_readiness / compliance).
    syntexa_chat_policy_path: str | None = Field(
        default=None,
        validation_alias="SYNTEXA_CHAT_POLICY_PATH",
        description="Caminho opcional para syntexa_chat_policy.json (absoluto ou relativo à raiz do repo).",
    )
    syntexa_chat_policy_profile: str | None = Field(
        default=None,
        validation_alias="SYNTEXA_CHAT_POLICY_PROFILE",
        description="Força perfil: development | staging | production (senão deriva de ENVIRONMENT).",
    )
    # Congelamento de promoções LLM (blue/green, canary): exige header X-Syntexa-Freeze-Bypass.
    llm_promotion_change_freeze: bool = Field(
        default=False,
        validation_alias="LLM_PROMOTION_CHANGE_FREEZE",
    )
    llm_promotion_freeze_bypass_secret: str | None = Field(
        default=None,
        validation_alias="LLM_PROMOTION_FREEZE_BYPASS_SECRET",
    )
    own_model_watchdog_enabled: bool = Field(
        default=True,
        validation_alias="OWN_MODEL_WATCHDOG_ENABLED",
    )
    own_model_watchdog_interval_sec: float = Field(
        default=60.0,
        validation_alias="OWN_MODEL_WATCHDOG_INTERVAL_SEC",
    )
    autonomy_evolution_loop_enabled: bool = Field(
        default=False,
        validation_alias="AUTONOMY_EVOLUTION_LOOP_ENABLED",
    )
    autonomy_evolution_interval_sec: int = Field(
        default=1800,
        validation_alias="AUTONOMY_EVOLUTION_INTERVAL_SEC",
    )
    autonomy_evolution_benchmark_suite_path: str = Field(
        default="config/domain_benchmark_suite.jsonl",
        validation_alias="AUTONOMY_EVOLUTION_BENCHMARK_SUITE_PATH",
    )
    autonomy_evolution_report_path: str = Field(
        default="docs/DOMAIN_BENCHMARK_REPORT.json",
        validation_alias="AUTONOMY_EVOLUTION_REPORT_PATH",
    )
    autonomy_evolution_scoreboard_path: str = Field(
        default="config/llm_quality_scoreboard.json",
        validation_alias="AUTONOMY_EVOLUTION_SCOREBOARD_PATH",
    )
    autonomy_evolution_comparison_path: str = Field(
        default="docs/LLM_FINAL_COMPARISON.md",
        validation_alias="AUTONOMY_EVOLUTION_COMPARISON_PATH",
    )

    # Fase 3 — estabilidade sob pico (sem infra nova)
    global_max_concurrent_llm: int = Field(default=32, validation_alias="GLOBAL_MAX_CONCURRENT_LLM")
    per_user_max_concurrent_llm: int = Field(default=5, validation_alias="PER_USER_MAX_CONCURRENT_LLM")
    slot_timeout_gov_sec: float = Field(default=300.0, validation_alias="SLOT_TIMEOUT_GOV_SEC")
    slot_timeout_auth_sec: float = Field(default=120.0, validation_alias="SLOT_TIMEOUT_AUTH_SEC")
    slot_timeout_public_sec: float = Field(default=75.0, validation_alias="SLOT_TIMEOUT_PUBLIC_SEC")
    load_stress_weight_cpu: float = Field(default=0.55, validation_alias="LOAD_STRESS_WEIGHT_CPU")
    load_stress_weight_mem: float = Field(default=0.45, validation_alias="LOAD_STRESS_WEIGHT_MEM")
    load_degrade_scale_min: float = Field(default=0.52, validation_alias="LOAD_DEGRADE_SCALE_MIN")
    load_queue_stress_threshold: float = Field(default=0.78, validation_alias="LOAD_QUEUE_STRESS_THRESHOLD")
    load_gov_boost_scale: float = Field(default=0.12, validation_alias="LOAD_GOV_BOOST_SCALE")
    session_create_per_ip_hour: int = Field(default=40, validation_alias="SESSION_CREATE_PER_IP_HOUR")
    integration_token_rpm: int = Field(
        default=60,
        validation_alias="INTEGRATION_TOKEN_RPM",
    )
    # Azure Storage: fila para pipeline de imagens + blob opcional para artefatos
    azure_storage_connection_string: str | None = Field(
        default=None, validation_alias="AZURE_STORAGE_CONNECTION_STRING"
    )
    azure_storage_image_queue: str = Field(
        default="image-jobs", validation_alias="AZURE_STORAGE_IMAGE_QUEUE"
    )
    azure_storage_image_container: str | None = Field(
        default=None, validation_alias="AZURE_STORAGE_IMAGE_CONTAINER"
    )
    generated_files_dir: str | None = Field(
        default=None,
        validation_alias="GENERATED_FILES_DIR",
        description="Diretório para ficheiros .ods gerados (default: <temp>/syntexa_generated).",
    )

    # ── WhatsApp Integration Settings ──────────────────────────────────
    WHATSAPP_META_APP_ID: str | None = Field(
        default=None,
        validation_alias="WHATSAPP_META_APP_ID",
        description="Meta App ID para OAuth de WhatsApp",
    )
    WHATSAPP_META_APP_SECRET: str | None = Field(
        default=None,
        validation_alias="WHATSAPP_META_APP_SECRET",
        description="Meta App Secret para WhatsApp OAuth",
    )
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = Field(
        default="syntexa_whatsapp_webhook_token_v1",
        validation_alias="WHATSAPP_WEBHOOK_VERIFY_TOKEN",
        description="Token para verificar webhooks do WhatsApp",
    )
    WHATSAPP_ACCESS_TOKEN: str | None = Field(
        default=None,
        validation_alias="WHATSAPP_ACCESS_TOKEN",
        description="Access token Meta obtido após OAuth",
    )
    WHATSAPP_BUSINESS_ACCOUNT_ID: str | None = Field(
        default=None,
        validation_alias="WHATSAPP_BUSINESS_ACCOUNT_ID",
        description="WABA ID armazenado após OAuth",
    )
    WHATSAPP_PHONE_NUMBER_ID: str | None = Field(
        default=None,
        validation_alias="WHATSAPP_PHONE_NUMBER_ID",
        description="Phone Number ID armazenado após OAuth",
    )

    # ── TikTok Integration Settings ───────────────────────────────────
    TIKTOK_CLIENT_ID: str | None = Field(
        default=None,
        validation_alias="TIKTOK_CLIENT_ID",
        description="TikTok Client ID para OAuth",
    )
    TIKTOK_CLIENT_SECRET: str | None = Field(
        default=None,
        validation_alias="TIKTOK_CLIENT_SECRET",
        description="TikTok Client Secret para OAuth",
    )
    TIKTOK_REDIRECT_URI: str = Field(
        default="https://syntexabr.com.br/i18n/pt-BR/integrations/tiktok/callback",
        validation_alias="TIKTOK_REDIRECT_URI",
        description="TikTok OAuth redirect URI",
    )
    TIKTOK_ACCESS_TOKEN: str | None = Field(
        default=None,
        validation_alias="TIKTOK_ACCESS_TOKEN",
        description="TikTok access token obtido após OAuth",
    )
    TIKTOK_OPEN_ID: str | None = Field(
        default=None,
        validation_alias="TIKTOK_OPEN_ID",
        description="TikTok Open ID do usuário",
    )
    TIKTOK_REFRESH_TOKEN: str | None = Field(
        default=None,
        validation_alias="TIKTOK_REFRESH_TOKEN",
        description="TikTok refresh token para renovação",
    )

    @computed_field
    @property
    def frontend_origins(self) -> List[str]:
        return _parse_frontend_origins(self.frontend_origin_raw)

    @field_validator("default_llm", mode="before")
    @classmethod
    def _default_llm_normalize(cls, v: object) -> str:
        s = str(v or "").strip().lower()
        return s or "syntexa_native"


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

    # Gateway não carrega LLM local; pular validação de endpoint
    if bool(getattr(s, "gateway_mode", False)):
        return

    insecure_admin_pw = {"", "admin123", "password", "123456"}
    if (s.admin_password or "").strip() in insecure_admin_pw or len((s.admin_password or "").strip()) < 10:
        raise ValueError(
            "VEREDA_ADMIN_PASSWORD insegura para produção. "
            "Defina senha forte no .env."
        )

    # Exige LLM real em produção: não usar 'dummy'. Núcleo proprietário: syntexa_native (sem endpoint externo).
    default_llm = (s.default_llm or "").strip().lower()
    if default_llm in {"", "dummy"}:
        raise ValueError(
            "DEFAULT_LLM inválido para produção. Use 'syntexa_native' (motor proprietário) ou configure "
            "'ollama' / 'exllama' / 'azure_tgi' / 'remote' / 'local_http' com o endpoint no .env."
        )

    # Mapear default para variável de endpoint esperada (syntexa_native não exige URL externa)
    endpoint_ok = default_llm == "syntexa_native"
    if default_llm == "ollama":
        endpoint_ok = bool(s.ollama_endpoint and str(s.ollama_endpoint).strip())
    elif default_llm == "exllama":
        endpoint_ok = bool(s.exllama_endpoint and s.exllama_endpoint.strip())
    elif default_llm == "azure_tgi":
        endpoint_ok = bool(s.azure_tgi_endpoint and s.azure_tgi_endpoint.strip())
    elif default_llm == "azure_openai":
        endpoint_ok = bool(s.azure_openai_endpoint and s.azure_openai_endpoint.strip())
    elif default_llm == "remote":
        endpoint_ok = bool(s.remote_llm_endpoint and s.remote_llm_endpoint.strip())
    elif default_llm == "local_http":
        endpoint_ok = bool(s.local_llm_endpoint and s.local_llm_endpoint.strip())

    if not endpoint_ok:
        raise ValueError(
            f"DEFAULT_LLM={default_llm} selecionado, mas o endpoint correspondente não está configurado no .env."
        )


# NOTA: Validação de produção removida do import síncrono.
# Executar somente em runtime via startup event do FastAPI.
# Isso evita que o container Railway morra antes do healthcheck subir.
# def _validate_production_settings(...) → usar validate_runtime_settings() no startup.
