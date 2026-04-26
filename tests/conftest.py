"""
Test infrastructure for the service layer.

Strategy: real Tortoise ORM against an in-memory SQLite database. Each test gets
a fresh schema. Postgres-only ArrayField is monkey-patched to a JSON-backed
shim BEFORE any model module is imported.
"""

# ─── 1. Patch Postgres-only ArrayField BEFORE models import ──────────────────
import tortoise.contrib.postgres.fields as _pg_fields
from tortoise import fields as _tortoise_fields


class _ArrayFieldShim(_tortoise_fields.JSONField): #type: ignore
    """SQLite-friendly stand-in for tortoise's PostgreSQL ArrayField.

    Models write `path_array = ArrayField(element_type="text", null=True)`;
    we just need *any* field that round-trips a Python list. JSON does that.
    """

    def __init__(self, element_type=None, **kwargs):
        kwargs.pop("element_type", None)
        super().__init__(**kwargs)


_pg_fields.ArrayField = _ArrayFieldShim #type: ignore


# ─── 2. Standard imports (now safe to touch the model layer) ─────────────────
import pytest
import pytest_asyncio
from tortoise import Tortoise


TORTOISE_TEST_CONFIG = {
    "connections": {"default": "sqlite://:memory:"},
    "apps": {
        "models": {
            "models": ["src.data.models"],
            "default_connection": "default",
        },
    },
}


@pytest_asyncio.fixture(autouse=True)
async def _init_db():
    """Fresh in-memory DB per test. Autouse so every test gets isolation."""
    await Tortoise.init(config=TORTOISE_TEST_CONFIG)
    await Tortoise.generate_schemas()
    try:
        yield
    finally:
        await Tortoise.close_connections()


# ─── 3. Helpers ──────────────────────────────────────────────────────────────
@pytest.fixture
def silence_logger(mocker):
    """Quiet loguru in tests that assert on logging side effects elsewhere."""
    return mocker.patch("loguru.logger")
