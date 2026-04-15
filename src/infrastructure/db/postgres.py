from src.infrastructure.config.settings import settings

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "dsn": settings.database_url,
            },
            "minsize": 5,
            "maxsize": 20,
            "max_inactive_connection_lifetime": 300,
        },
    },
    "apps": {
        "models": {
            "models": ["src.data.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
