from src.infrastructure.db.pool import get_pool, init_pool, close_pool
import pytest
import asyncpg

async def test_access_pool_before_initialization(
    clean_pool_state
):
    with pytest.raises(RuntimeError, match="pool"):
        pool = get_pool()

async def test_double_init_pool(
    clean_pool_state
):
    pool_a = await init_pool()
    pool_b = await init_pool()
    assert pool_a is pool_b

async def test_double_close_pool(
    clean_pool_state
):
    pool = await init_pool()
    await close_pool()
    await close_pool()
    with pytest.raises(RuntimeError):
        pool = get_pool()

async def test_jsonb_codec(
    db_pool: asyncpg.Pool,
    jsonb_table
):

    value_1 = {"key": "value"}
    value_2 = {
        "key1": {
            "key2": [1, 2, 3],
            "key3": {
                "key4": [[1], [2], [3]]
            }
        }
    }
    
    await db_pool.execute(
        """
        INSERT INTO _test_jsonb (data)
        VALUES
            ($1),
            ($2),
            (NULL)
        """,
        value_1,
        value_2
    )

    rows = await db_pool.fetch("SELECT * FROM _test_jsonb")

    assert rows[0]["data"] == value_1
    assert rows[1]["data"] == value_2
    assert rows[2]["data"] == None
