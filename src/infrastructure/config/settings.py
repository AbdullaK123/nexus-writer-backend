from pathlib import Path
from functools import lru_cache
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Secrets + env-varying values (.env) ──────────────────────────────────────

class Settings(BaseSettings):
    """Deployment-specific: secrets + values that vary between dev/staging/prod.
    Loaded from .env file only."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        frozen=True,
        extra="ignore",
    )

    # Connection strings
    database_url: str
    database_sync_url: str
    migration_url: str
    mongodb_url: str
    motherduck_url: str
    redis_url: str
    redis_broker_url: str

    # Crypto keys
    app_secret_key: str
    cookie_signing_key: str
    cookie_encryption_key: str

    # External API keys
    openai_api_key: str
    gemini_api_key: str

    # Environment
    env: str = "dev"
    debug: bool = False

    # Service URLs (vary per deployment)
    prefect_api_url: str | None = None
    ollama_base_url: str = "http://localhost:11434/v1"

    # Feature flags
    use_lfm: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]


# ── Static application config (config.yaml) ─────────────────────────────────

class AuthConfig(BaseModel, frozen=True):
    password_pattern: str = r'^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()_+\-=\[\]{};:\x27"\\|,.<>/?]).{8,}$'


class PrefectConfig(BaseModel, frozen=True):
    task_retries: int = 1
    task_retry_delay: int = 10
    extraction_task_timeout: int = 120
    chapter_flow_timeout: int = 180
    result_storage_ttl: int = 86400


class AIConfig(BaseModel, frozen=True):
    model: str = "google/gemini-2.5-flash"
    lite_model: str = "google/gemini-2.5-flash-lite"
    temperature: float = 0.7
    max_tokens: int = 4096
    sdk_timeout: int = 90
    sdk_retries: int = 2


class OllamaConfig(BaseModel, frozen=True):
    model: str = "lfm2-1.2b-extract"


class Config(BaseModel, frozen=True):
    """Application-wide static configuration. Loaded from config.yaml."""

    auth: AuthConfig = AuthConfig()
    prefect: PrefectConfig = PrefectConfig()
    ai: AIConfig = AIConfig()
    ollama: OllamaConfig = OllamaConfig()


# ── Loader ───────────────────────────────────────────────────────────────────

def _load_yaml_config() -> dict[str, Any]:
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


@lru_cache
def _load() -> tuple[Settings, Config]:
    s = Settings()
    yaml_data = _load_yaml_config()
    c = Config(**yaml_data)
    return s, c


settings, config = _load()


# ── FastAPI dependencies ─────────────────────────────────────────────────────

def get_settings() -> Settings:
    """FastAPI dependency. Override in tests via app.dependency_overrides."""
    return settings


def get_config() -> Config:
    """FastAPI dependency. Override in tests via app.dependency_overrides."""
    return config
