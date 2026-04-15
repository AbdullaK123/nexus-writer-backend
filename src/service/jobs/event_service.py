from typing import AsyncIterator

from src.data.schemas.jobs import FlowEvent, FlowEventType
from src.infrastructure.redis.pubsub import RedisPubSub


class JobEventService:
    def __init__(self, redis_url: str):
        self._redis_url = redis_url

    async def stream_events(self, user_id: str, job_id: str) -> AsyncIterator[FlowEvent]:
        pubsub = RedisPubSub(self._redis_url, FlowEvent)
        channel = pubsub.channel("flow", user_id, job_id)
        async for event in pubsub.subscribe(channel):
            yield event
            if event.event_type in (FlowEventType.FLOW_COMPLETE, FlowEventType.FLOW_FAILED):
                break