from typing import AsyncIterator, Iterator
import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import AsyncRedisContainer
from redis.asyncio import Redis
from src.infrastructure.redis.pubsub import RedisPubSub
from src.infrastructure.db.pool import _setup_connection, close_pool
from src.infrastructure.redis.pool import close_pool as close_redis_pool
from src.infrastructure.config import config
import asyncpg
import logging
from loguru import logger

@pytest.fixture(scope="session")
def postgres_container() -> Iterator[PostgresContainer]:
    with PostgresContainer(
        "pgvector/pgvector:pg18",
        driver=None
    ) as postgres:
        yield postgres

@pytest.fixture(scope="session")
def redis_container() -> Iterator[AsyncRedisContainer]:
    with AsyncRedisContainer(
        "redis:latest"
    ) as redis:
        yield redis

@pytest.fixture(scope="session")
def postgres_url(
    postgres_container: PostgresContainer
) -> str:
    dsn =  postgres_container.get_connection_url()
    return dsn.replace("postgresql+psycopg2://", "postgresql://")

@pytest.fixture(scope="session")
def redis_url(
    redis_container: AsyncRedisContainer,
) -> str:
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}/0"


@pytest_asyncio.fixture
async def redis_client(
    redis_url: str,
) -> AsyncIterator[Redis]:
    
    client = Redis.from_url(
        redis_url,
        decode_responses=True,
    )

    await client.flushdb()

    try:
        yield client
    finally:
        await client.flushdb()
        await client.aclose()

@pytest_asyncio.fixture
async def redis_pubsub(
    redis_client: Redis
) -> AsyncIterator[RedisPubSub]:
    yield RedisPubSub(redis_client)


@pytest_asyncio.fixture
async def db_pool(
    postgres_url: str
) -> AsyncIterator[asyncpg.Pool]:

    pool = await asyncpg.create_pool(
        dsn=postgres_url,
        min_size=config.postgres.pool_min_size,
        max_size=config.postgres.pool_max_size,
        max_inactive_connection_lifetime=config.postgres.max_inactive_connection_lifetime,
        init=_setup_connection
    )

    try:
        yield pool
    finally:
        await pool.close()


@pytest_asyncio.fixture
async def clean_pool_state(
    postgres_url: str,
    monkeypatch: pytest.MonkeyPatch
):
    from src.infrastructure.config import settings
    
    test_settings = settings.model_copy(update={"database_url": postgres_url})

    monkeypatch.setattr("src.infrastructure.db.pool.settings", test_settings)

    yield
    
    await close_pool()


@pytest_asyncio.fixture
async def clean_infra_state(
    postgres_url: str,
    redis_url: str,
    monkeypatch: pytest.MonkeyPatch
):
    from src.infrastructure.config import settings
    
    test_settings = settings.model_copy(update={"database_url": postgres_url, "redis_url": redis_url})

    monkeypatch.setattr("src.infrastructure.db.pool.settings", test_settings)

    yield
    
    try:
        await close_pool()
    except Exception:
        pass

    try:
        await close_redis_pool()
    except Exception:
        pass

@pytest_asyncio.fixture
async def jsonb_table(db_pool: asyncpg.Pool):
    await db_pool.execute("""
        CREATE TABLE IF NOT EXISTS _test_jsonb (
            id serial PRIMARY KEY,
            data jsonb
        )
    """)
    yield
    await db_pool.execute("DROP TABLE IF EXISTS _test_jsonb")

@pytest.fixture(autouse=True)
def propagate_logs_to_caplog():
    """Propagate Loguru logs to standard logging so pytest caplog works."""
    # Define a handler that sends log records to standard logging
    class PropagateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    # Add the handler to Loguru
    sink_id = logger.add(PropagateHandler(), format="{message}")
    
    yield
    
    # Clean up the handler after the test ends
    logger.remove(sink_id)