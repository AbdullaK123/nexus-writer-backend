from typing import Any, List

from redis.asyncio import Redis

from src.data.schemas.jobs import FlowEvent


class JobEventService:
    def __init__(self, redis_url: str):
        self._redis = Redis.from_url(redis_url)

    async def drain(self, user_id: str) -> List[FlowEvent[Any]]:
        """Pop all pending events for a user from the Redis list atomically."""
        key = f"flow:{user_id}"
        pipe = self._redis.pipeline()
        pipe.lrange(key, 0, -1)
        pipe.delete(key)
        results = await pipe.execute()
        raw_events: list[bytes] = results[0]
        return [FlowEvent.model_validate_json(raw) for raw in raw_events]