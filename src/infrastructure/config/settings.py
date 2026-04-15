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
    session_ttl_days: int = 1
    cookie_max_age_seconds: int = 86400


class HttpConfig(BaseModel, frozen=True):
    max_body_size_bytes: int = 10 * 1024 * 1024


class PostgresConfig(BaseModel, frozen=True):
    pool_min_size: int = 5
    pool_max_size: int = 20
    max_inactive_connection_lifetime: int = 300


class RedisConfig(BaseModel, frozen=True):
    socket_connect_timeout: int = 5
    socket_timeout: int = 5


class JobsConfig(BaseModel, frozen=True):
    session_cleanup_batch_size: int = 1000
    session_cleanup_cron: str = "0 * * * *"
    line_edits_cooldown_hours: int = 24
    estimated_extraction_duration_seconds: int = 60


class AnalyticsConfig(BaseModel, frozen=True):
    session_cache_ttl_seconds: int = 3600


class PrefectConfig(BaseModel, frozen=True):
    task_retries: int = 1
    task_retry_delay: int = 10
    extraction_task_timeout: int = 120
    chapter_flow_timeout: int = 180
    result_storage_ttl: int = 86400
    extraction_deployment: str = "extract-single-chapter/chapter-extraction-deployment"
    line_edits_deployment: str = "line-edits/line-edits-deployment"
    reextraction_deployment: str = "reextraction-flow/chapter-reextraction-deployment"
    predecessor_poll_interval: int = 5
    predecessor_max_wait: int = 600


class AIConfig(BaseModel, frozen=True):
    model: str = "google/gemini-2.5-flash"
    lite_model: str = "google/gemini-2.5-flash-lite"
    temperature: float = 0.7
    max_tokens: int = 4096
    sdk_timeout: int = 90
    sdk_retries: int = 2


class OllamaConfig(BaseModel, frozen=True):
    model: str = "lfm2-1.2b-extract"


class MongoConfig(BaseModel, frozen=True):
    database_name: str = "nexus_extractions"


class Config(BaseModel, frozen=True):
    """Application-wide static configuration. Loaded from config.yaml."""

    auth: AuthConfig = AuthConfig()
    http: HttpConfig = HttpConfig()
    postgres: PostgresConfig = PostgresConfig()
    redis: RedisConfig = RedisConfig()
    jobs: JobsConfig = JobsConfig()
    analytics: AnalyticsConfig = AnalyticsConfig()
    prefect: PrefectConfig = PrefectConfig()
    ai: AIConfig = AIConfig()
    ollama: OllamaConfig = OllamaConfig()
    mongo: MongoConfig = MongoConfig()


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
