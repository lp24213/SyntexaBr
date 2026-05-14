from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(_REPO_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="allow",
    )

    project_name: str = "Syntexa Local Private AI"
    environment: str = Field(default="local", validation_alias="ENVIRONMENT")

    # Ollama
    ollama_endpoint: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_ENDPOINT")
    ollama_api_key: str | None = Field(default=None, validation_alias="OLLAMA_API_KEY")
    ollama_default_model: str = Field(default="llama3", validation_alias="OLLAMA_DEFAULT_MODEL")

    # Private models path
    private_models_path: str | None = Field(default=None, validation_alias="PRIVATE_MODELS_PATH")

    # Security
    api_key: str | None = Field(default=None, validation_alias="LOCAL_AI_API_KEY")


settings = Settings()
