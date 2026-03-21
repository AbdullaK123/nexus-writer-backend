from functools import lru_cache

from pydantic import Field
from pydantic_settings import SettingsConfigDict, BaseSettings
class Config(BaseSettings):

    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=False,
        frozen=True,
        strict=True,
        extra='ignore'
    )

    motherduck_url: str = Field(..., description='Our analytics dw connections string')
    database_url: str = Field(..., description='Our postgres connection string')
    mongodb_url: str = Field(..., description='The mongodb connection string for ai extractions')
    database_sync_url: str = Field(..., description='Our sync postgres connection for migrations')
    migration_url: str = Field(..., description='database uri for migrations')
    app_secret_key: str = Field(..., description='The secret key for password hashing')
    cookie_signing_key: str = Field(..., description='For verifying the signature of our encrypted session ids')
    cookie_encryption_key: str = Field(..., description='For encrypting our cookies')
    redis_url: str = Field(..., description="The uri for redis")
    redis_broker_url: str = Field(..., description="The uri for the redis_broker")
    openai_api_key: str = Field(..., description="OpenAI API key")
    gemini_api_key: str = Field(..., description="Gemini API KEY")
    env: str = Field(default='dev')
    debug: bool = Field(default=False)
    password_pattern: str = r"^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]).{8,}$"
    
    # Prefect configuration
    prefect_api_url: str | None = Field(default=None, description="Prefect server API URL")
    default_task_retries: int = Field(default=1, description="Prefect task retries (1 = one retry after failure)")
    default_task_retry_delay: int = Field(default=10, description="Delay before task retry in seconds")
    extraction_task_timeout: int = Field(default=120, description="Timeout for extraction tasks in seconds")
    chapter_flow_timeout: int = Field(default=180, description="Timeout for chapter extraction flow in seconds")
    result_storage_ttl: int = Field(default=86400, description="Result storage TTL in seconds (24 hours)")

    # AI / LLM settings
    ai_model: str = Field(default="google/gemini-2.5-flash", description="Primary LLM in provider/model format (google, openai, anthropic, ollama)")
    ai_lite_model: str = Field(default="google/gemini-2.5-flash-lite", description="Lightweight LLM for cheaper tasks in provider/model format")
    ai_temperature: float = Field(..., description="Temperature of the LLM")
    ai_maxtokens: int = Field(..., description="Max tokens to generate in structured outputs")
    ai_sdk_timeout: int = Field(default=90, description="HTTP timeout per LLM request in seconds")
    ai_sdk_retries: int = Field(default=2, description="SDK-level retries for transient HTTP errors")

    # Ollama / LFM settings
    use_lfm: bool = Field(default=False, description="Use Liquid Foundation Model via Ollama for parser nodes instead of Gemini")
    ollama_base_url: str = Field(default="http://localhost:11434/v1", description="Ollama API base URL (OpenAI-compatible)")
    ollama_model: str = Field(default="lfm2-1.2b-extract", description="Ollama model name for LFM extraction")


@lru_cache
def get_settings() -> Config:
    return Config()


app_config = get_settings()