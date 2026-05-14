from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(_REPO_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="allow",
    )

    project_name: str = "Syntexa AI Worker"
    environment: str = Field(default="local", validation_alias="ENVIRONMENT")
    cors_origins: List[str] = Field(default=["*"], validation_alias="CORS_ORIGINS")

    # Security
    api_key: str | None = Field(default=None, validation_alias="AI_WORKER_API_KEY")

    # Embeddings
    embedding_backend: str = Field(default="fastembed", validation_alias="EMBEDDING_BACKEND")
    fastembed_model_name: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        validation_alias="FASTEMBED_MODEL_NAME",
    )

    # LLM
    default_llm_model: str = Field(default="microsoft/DialoGPT-medium", validation_alias="DEFAULT_LLM_MODEL")
    huggingface_token: str | None = Field(default=None, validation_alias="HUGGINGFACE_TOKEN")
    local_model_path: str | None = Field(default=None, validation_alias="LOCAL_MODEL_PATH")

    # Ollama fallback
    ollama_endpoint: str | None = Field(default=None, validation_alias="OLLAMA_ENDPOINT")
    ollama_model: str | None = Field(default=None, validation_alias="OLLAMA_MODEL")

    # TTS
    edge_tts_voice: str = Field(default="pt-BR-FranciscaNeural", validation_alias="EDGE_TTS_VOICE")

    # OCR
    ocr_language: str = Field(default="por", validation_alias="OCR_LANGUAGE")

    # Whisper
    whisper_model_size: str = Field(default="base", validation_alias="WHISPER_MODEL_SIZE")

    # Rate limits
    max_requests_per_minute: int = Field(default=100, validation_alias="AI_WORKER_RPM")


settings = Settings()
