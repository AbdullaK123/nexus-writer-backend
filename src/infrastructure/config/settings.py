from pathlib import Path
from functools import lru_cache
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field, model_validator
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
    # Crypto keys
    app_secret_key: str = Field(min_length=32)

    # Environment
    env: Literal["dev", "staging", "prod"] = "dev"
    debug: bool = False

    # open ai api key
    openai_api_key: str

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    @model_validator(mode="after")
    def validate_cors(self):
        if self.cors_allow_credentials and "*" in self.cors_origins:
            raise ValueError(
                "cors_allow_credentials=True is incompatible with wildcard origins"
            )
        return self

    @model_validator(mode="after")
    def no_debug_in_prod(self):
        if self.env == "prod" and self.debug:
            raise ValueError("debug mode must be off in prod")
        return self


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


class AiConfig(BaseModel, frozen=True):
    default_model: str = "gpt-5.4-nano-2026-03-17"
    embedding_model: str = "text-embedding-3-small"
    # How many scenes a single embedding cron tick will pull and embed.
    # Lower bound 1 (no point running otherwise); upper bound 128 keeps any
    # one tick small enough that a worker crash loses little work and stays
    # well under provider per-request limits (OpenAI: 2048 inputs / ~300k
    # tokens; Voyage/Cohere: ~96-128). Sequential DB writes mean wall-clock
    # roughly scales linearly with this value.
    embedding_batch_size: int = Field(default=32, ge=1, le=128)
    temperature: float = 0.0
    max_retries: int = 3
    timeout: float = 300.0
    max_concurrent_requests: int = 16
    scene_extraction_max_tokens: int = 8000
    pulse_extraction_max_tokens: int = 8000
    summarization_max_tokens: int = 2000
    extraction_retry_attempts: int = 3
    extraction_retry_wait_seconds: float = 1.0


class SearchConfig(BaseModel, frozen=True):
    """Tunables for hybrid scene search.

    `default_k` — top-N hits returned when caller omits `k`.
    `default_candidate_pool` — how many rows each of the FTS / vector CTEs
    pull before RRF fuses + truncates. Bigger pool = more chance the two
    channels overlap on the same scene (which is what amplifies score), at
    the cost of more rows scanned per query.
    """
    default_k: int = Field(default=5, ge=1, le=50)
    default_candidate_pool: int = Field(default=50, ge=1, le=500)


class JobConfig(BaseModel, frozen=True):
    session_cleanup_cron_expression: str = "0 * * * *"
    scene_extraction_cron_expression: str = "0 */2 * * * *"
    scene_extraction_batch_size: int = 5
    scene_extraction_window_seconds: int = 60
    # Runs every minute (6-field cron, seconds-precision via aiocron). Embedding
    # is cheap and idempotent — scenes with embedding IS NULL are the queue,
    # so a frequent tick keeps newly-extracted scenes searchable quickly.
    # Offset 30s from the extraction cron (which fires at :00 every 2 min) so
    # the two jobs don't fight for the same connections.
    scene_embedding_cron_expression: str = "30 * * * * *"

class Config(BaseModel, frozen=True):
    """Application-wide static configuration. Loaded from config.yaml."""

    auth: AuthConfig = AuthConfig()
    http: HttpConfig = HttpConfig()
    postgres: PostgresConfig = PostgresConfig()
    ai: AiConfig = AiConfig()
    jobs: JobConfig = JobConfig()
    search: SearchConfig = SearchConfig()


# ── Loader ───────────────────────────────────────────────────────────────────


def _load_yaml_config() -> dict[str, Any]:
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


@lru_cache
def _load() -> tuple[Settings, Config]:
    s = Settings()  # type: ignore
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
