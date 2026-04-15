from src.infrastructure.config.settings import settings, config

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "dsn": settings.database_url,
            },
            "minsize": config.postgres.pool_min_size,
            "maxsize": config.postgres.pool_max_size,
            "max_inactive_connection_lifetime": config.postgres.max_inactive_connection_lifetime,
        },
    },
    "apps": {
        "models": {
            "models": ["src.data.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
