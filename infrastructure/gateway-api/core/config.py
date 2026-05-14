from pathlib import Path
from typing import List

from pydantic import EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _parse_frontend_origins(v: object) -> List[str]:
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

    project_name: str = "Syntexa Gateway"
    api_v1_prefix: str = "/v1"
    environment: str = Field(default="local", validation_alias="ENVIRONMENT")

    frontend_origin_raw: str = Field(default="*", validation_alias="FRONTEND_ORIGIN")

    secret_key: str = Field(default="dev-secret-key-change-me", validation_alias="VEREDA_SECRET_KEY")
    admin_email: str = Field(default="admin@syntexa.dev", validation_alias="VEREDA_ADMIN_EMAIL")
    admin_password: str = Field(default="admin123", validation_alias="VEREDA_ADMIN_PASSWORD")

    # Stripe
    stripe_secret_key: str = Field(default="", validation_alias="STRIPE_SECRET_KEY")
    stripe_price_basic: str = Field(default="", validation_alias="STRIPE_PRICE_BASIC")
    stripe_price_medium: str = Field(default="", validation_alias="STRIPE_PRICE_MEDIUM")
    stripe_price_master: str = Field(default="", validation_alias="STRIPE_PRICE_MASTER")
    stripe_webhook_secret: str = Field(default="", validation_alias="STRIPE_WEBHOOK_SECRET")
    frontend_base_url: str = Field(default="https://syntexabr.com.br", validation_alias="FRONTEND_BASE_URL")
    api_public_base_url: str = Field(default="https://api.syntexabr.com.br", validation_alias="API_PUBLIC_BASE_URL")

    # AI Worker endpoints (Kaggle / GPU / Local)
    ai_worker_url: str | None = Field(default=None, validation_alias="AI_WORKER_URL")
    ai_worker_api_key: str | None = Field(default=None, validation_alias="AI_WORKER_API_KEY")
    local_ai_url: str | None = Field(default=None, validation_alias="LOCAL_AI_URL")
    local_ai_api_key: str | None = Field(default=None, validation_alias="LOCAL_AI_API_KEY")

    # Ollama (fallback)
    ollama_endpoint: str | None = Field(default=None, validation_alias="OLLAMA_ENDPOINT")
    ollama_api_key: str | None = Field(default=None, validation_alias="OLLAMA_API_KEY")

    # Redis (lightweight cache / pub-sub only)
    redis_url: str | None = Field(default=None, validation_alias="REDIS_URL")

    # DB (lightweight gateway may skip DB for health, but needed for auth/admin)
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")

    # Rate limiting
    rate_limit_requests_per_minute: int = Field(default=60, validation_alias="RATE_LIMIT_RPM")

    require_cloudflare: bool = Field(default=False, validation_alias="REQUIRE_CLOUDFLARE")

    @field_validator("frontend_origin_raw", mode="before")
    @classmethod
    def _validate_origins(cls, v):
        return _parse_frontend_origins(v)

    @property
    def frontend_origins(self) -> List[str]:
        return _parse_frontend_origins(self.frontend_origin_raw)


settings = Settings()
