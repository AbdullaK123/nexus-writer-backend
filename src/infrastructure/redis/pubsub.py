from typing import TypeVar, Generic, AsyncIterator, Type
from pydantic import BaseModel
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

T = TypeVar("T", bound=BaseModel)

class RedisPubSub(Generic[T]):
    def __init__(self, url: str, model: Type[T]):
        self.client = Redis.from_url(url)
        self.model  = model

    async def publish(self, channel: str, event: T) -> None:
        await self.client.publish(channel, event.model_dump_json())

    async def subscribe(self, channel: str) -> AsyncIterator[T]:
        pubsub = self.client.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                yield self.model.model_validate_json(message["data"])
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.aclose()
            except (RedisConnectionError, ConnectionResetError, OSError):
                pass

    async def close(self) -> None:
        await self.client.aclose()

    def channel(self, *parts: str) -> str:
        return ":".join(parts)  