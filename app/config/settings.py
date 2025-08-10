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
    env: str = Field(default='dev')
    debug: bool = Field(default=False)
    password_pattern: str = r"^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]).{8,}$"


app_config = Config()