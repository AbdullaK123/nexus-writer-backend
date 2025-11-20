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
    migration_url: str = Field(..., description='database uri for migrations')
    app_secret_key: str = Field(..., description='The secret key for password hashing')
    cookie_signing_key: str = Field(..., description='For verifying the signature of our encrypted session ids')
    cookie_encryption_key: str = Field(..., description='For encrypting our cookies')
    redis_url: str = Field(..., description="The uri for redis")
    # Default RabbitMQ URL for local/dev environments; override via env RABBITMQ_URL
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/", description="The uri for rabbitmq")
    # Optional OpenAI API key for prose agent; if not set, the /chapters/ai/edit endpoint will raise a clear error when invoked
    openai_api_key: str | None = Field(default=None, description="OpenAI API key used by the prose agent")
    env: str = Field(default='dev')
    debug: bool = Field(default=False)
    password_pattern: str = r"^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]).{8,}$"
    neo4j_url: str = Field(..., description="The uri for neo4j")
    neo4j_user: str = Field(..., description="The username for neo4j")
    neo4j_password: str = Field(..., description="The password for neo4j")


app_config = Config()