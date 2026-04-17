from urllib.parse import urlencode, urlparse, urlunparse
from src.infrastructure.config.settings import settings, config


def _build_database_url() -> str:
    pool_params = urlencode({
        "minsize": config.postgres.pool_min_size,
        "maxsize": config.postgres.pool_max_size,
        "max_inactive_connection_lifetime": config.postgres.max_inactive_connection_lifetime,
    })
    parsed = urlparse(settings.database_url)
    existing_query = f"{parsed.query}&{pool_params}" if parsed.query else pool_params
    return urlunparse(parsed._replace(query=existing_query))


TORTOISE_ORM = {
    "connections": {
        "default": _build_database_url(),
    },
    "apps": {
        "models": {
            "models": ["src.data.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
