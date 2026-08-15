from redis.asyncio import Redis, ConnectionError
from src.infrastructure.redis.pubsub import RedisPubSub
from pydantic import BaseModel
import asyncio
import pytest
import json
from typing import List


@pytest.mark.parametrize("bad_payload", [
    "I am garbage", 
    json.dumps({"wrong_field": "Bad data"})
])
async def test_listener_skips_bad_data(
    bad_payload,
    redis_client: Redis,
    redis_pubsub: RedisPubSub
):

    class TestSchema(BaseModel):
        data: str

    received: List[TestSchema] = []

    async def consume[T: BaseModel](
        pubsub: RedisPubSub, 
        channel: str, 
        schema: type[T]
    ):
        async for msg in pubsub.listen(channel, schema):
            received.append(msg) # type: ignore

    task = asyncio.create_task(consume(redis_pubsub, "test-channel", TestSchema))
    await asyncio.sleep(0.1)

    await redis_client.publish("test-channel", bad_payload)
    await redis_client.publish("test-channel", TestSchema(data="valid").model_dump_json())
    await asyncio.sleep(0.1)

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert len(received) == 1
    assert received[0].data == "valid"

async def test_cleanup(
    redis_pubsub: RedisPubSub
):

    class TestSchema(BaseModel):
        data: str
    
    received = []
    
    async def consume[T: BaseModel](
        pubsub: RedisPubSub, 
        channel: str, 
        schema: type[T]
    ):
        async for msg in pubsub.listen(channel, schema):
            received.append(msg)    

    task = asyncio.create_task(consume(redis_pubsub, "test-channel", TestSchema))
    await asyncio.sleep(0.1)

    task.cancel()

    await redis_pubsub.publish("test-channel", TestSchema(data="test-data"))

    with pytest.raises(asyncio.CancelledError):
        await task

    assert len(received) == 0