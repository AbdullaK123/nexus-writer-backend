from src.infrastructure.config.settings import settings

TORTOISE_ORM = {
    "connections": {
        "default": settings.database_url,
    },
    "apps": {
        "models": {
            "models": ["src.data.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
