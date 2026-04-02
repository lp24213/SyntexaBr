#!/usr/bin/env python3
"""Substitui vereda_ai/core/config.py no servidor (Pydantic v2, frontend_origins + validator)."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "vereda_ai" / "core" / "config.py"

CONFIG_CONTENT = r'''from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    frontend_origins: str = ""

    secret_key: str = Field(default="dev-secret-key", validation_alias="VEREDA_SECRET")
    access_token_exp_hours: int = 12
    database_url: str = Field(
        default="sqlite:///./vereda_ai.db",
        validation_alias="VEREDA_DATABASE_URL",
    )
    default_llm: str = Field(default="ollama", validation_alias="DEFAULT_LLM")
    local_llm_endpoint: str | None = Field(
        default=None, validation_alias="LOCAL_LLM_ENDPOINT"
    )
    ollama_endpoint: str | None = Field(
        default=None, validation_alias="OLLAMA_ENDPOINT"
    )
    ollama_model: str = Field(default="mistral", validation_alias="OLLAMA_MODEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
'''


def main():
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(CONFIG_CONTENT, encoding="utf-8")
    print("vereda_ai/core/config.py substituído (frontend_origins + extra=ignore).")


if __name__ == "__main__":
    main()
