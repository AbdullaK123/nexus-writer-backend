import pytest
import asyncio
from src.app.dependencies.services import init_infrastructure, shutdown_infrastructure
from src.infrastructure.exceptions import InfrastructureError
import src.app.dependencies.services as services
from src.infrastructure.db.pool import get_pool as get_db_pool
from src.infrastructure.redis.pool import get_pool as get_redis_pool
from loguru import logger



async def test_db_failure(
    clean_infra_state,
    monkeypatch: pytest.MonkeyPatch
):
    async def db_goes_boom():
        raise Exception("KABOOM!")

    monkeypatch.setattr(services, "init_db_pool", db_goes_boom)

    with pytest.raises(InfrastructureError):
        await init_infrastructure()


async def test_redis_failure(
    clean_infra_state,
    monkeypatch: pytest.MonkeyPatch
):
    def redis_goes_boom():
        raise Exception("KABOOM!")

    monkeypatch.setattr(services, "init_redis_pool", redis_goes_boom)

    with pytest.raises(InfrastructureError):
        await init_infrastructure()

    with pytest.raises(RuntimeError, match="pool not initialised"):
        get_db_pool()


async def test_db_clean_up_on_redis_failure_disaster(
    clean_infra_state,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,  # 1. Add caplog fixture
):
    def redis_goes_boom():
        raise Exception("KABOOM!")

    async def db_clean_up_fails():
        raise Exception("Pool refuses to die")

    monkeypatch.setattr(services, "init_redis_pool", redis_goes_boom)
    monkeypatch.setattr(services, "close_db_pool", db_clean_up_fails)

    with pytest.raises(InfrastructureError):
        await init_infrastructure()

    # 2. Assert against the text captured inside caplog
    assert "init_infrastructure.cleanup_failed" in caplog.text

    with pytest.raises(RuntimeError, match="pool not initialized"):
        get_redis_pool()


async def test_db_clean_up_failure(
    clean_infra_state,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,  
):
    async def db_clean_up_fails():
        raise Exception("Pool refuses to die")

    monkeypatch.setattr(services, "close_db_pool", db_clean_up_fails)

    await init_infrastructure()

    await shutdown_infrastructure()

    assert "shutdown_infrastructure.failed" in caplog.text


    with pytest.raises(RuntimeError, match="pool not initialized"):
        get_redis_pool()


async def test_redis_clean_up_failure(
    clean_infra_state,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,  
):
    async def redis_clean_up_fails():
        raise Exception("Pool refuses to die")

    monkeypatch.setattr(services, "close_redis_pool", redis_clean_up_fails)

    await init_infrastructure()

    await shutdown_infrastructure()

    assert "shutdown_infrastructure.failed" in caplog.text

    with pytest.raises(RuntimeError, match="pool not initialised"):
        get_db_pool()

