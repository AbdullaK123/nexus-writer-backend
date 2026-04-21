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
    cors_origins: list[str] = ["http://localhost:3000"]
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


class SummaryTokenConfig(BaseModel, frozen=True):
    character: int = 600
    plot: int = 600
    world: int = 500
    style: int = 200


class ExtractionTokenConfig(BaseModel, frozen=True):
    character: int = 18000
    plot_threads: int = 8000
    world_bible: int = 40000
    voice: int = 4000


class TokenConfig(BaseModel, frozen=True):
    summary: SummaryTokenConfig = SummaryTokenConfig()
    extraction: ExtractionTokenConfig = ExtractionTokenConfig()


class AiConfig(BaseModel, frozen=True):
    max_tokens: TokenConfig = TokenConfig()
    temperature: float = 0.0
    default_model: str = "gpt-5.4-nano-2026-03-17"
    max_retries: int = 3
    timeout: float = 300.0
    max_concurrent_requests: int = 16
    regeneration_batch_size: int = 20
    regeneration_cron_expression: str = "0 * * * *"
    extraction_cron_expression: str = "*/10 * * * * *"


class JobConfig(BaseModel, frozen=True):
    session_cleanup_batch_size: int = 1000
    session_cleanup_cron_expression: str = "0 */6 * * *"
    mark_stale_word_count_delta: int = 1000

class Config(BaseModel, frozen=True):
    """Application-wide static configuration. Loaded from config.yaml."""

    auth: AuthConfig = AuthConfig()
    http: HttpConfig = HttpConfig()
    postgres: PostgresConfig = PostgresConfig()
    ai: AiConfig = AiConfig()
    jobs: JobConfig = JobConfig()


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
