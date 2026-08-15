import asyncio
from typing import AsyncGenerator

import redis.asyncio as aioredis
from loguru import logger
from pydantic import BaseModel, ValidationError



class RedisPubSub:

    def __init__(self, redis: aioredis.Redis):
        self.client = redis

    async def publish(self, channel: str, payload: BaseModel) -> None:
        subscriber_count = await self.client.publish(channel, payload.model_dump_json())
        logger.debug(
            "infra.redis_pubsub.published",
            channel=channel,
            payload_type=type(payload).__name__,
            subscriber_count=subscriber_count,
        )

    async def listen[T: BaseModel](self, channel: str, schema: type[T]) -> AsyncGenerator[T, None]:

        pubsub = self.client.pubsub()

        await pubsub.subscribe(channel)

        logger.info(
            "infra.redis_pubsub.subscribed",
            channel=channel,
            schema=schema.__name__,
        )

        try:
            async for message in pubsub.listen():
                if message['type'] == "message":
                    logger.debug(
                        "infra.redis_pubsub.message_received",
                        channel=channel,
                        schema=schema.__name__,
                    )
                    try:
                        yield schema.model_validate_json(message['data'])
                    except ValidationError:
                        logger.warning(
                            "infra.redis_pubsub.bad_payload",
                            channel=channel,
                            payload=message['data']
                        )
                        continue
        except asyncio.CancelledError:
            logger.debug(
                "infra.redis_pubsub.listen_cancelled",
                channel=channel,
                schema=schema.__name__,
            )
            raise
        except Exception:
            logger.exception(
                "infra.redis_pubsub.listen_failed",
                channel=channel,
                schema=schema.__name__,
            )
            raise
        finally:
            await pubsub.unsubscribe()
            await pubsub.aclose()
            logger.info(
                "infra.redis_pubsub.unsubscribed",
                channel=channel,
                schema=schema.__name__,
            )
