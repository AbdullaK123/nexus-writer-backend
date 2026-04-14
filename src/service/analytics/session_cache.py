from redis import Redis
from src.infrastructure.utils.retry import retry_redis
from src.data.schemas.analytics import WritingSessionEvent
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)
from datetime import datetime
import json


class SessionCacheService:

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    @retry_redis
    def save(self, sid: str, data: dict) -> None:
        redis_key = f"analytics_session:{sid}"
        serializable_data = {}
        for key, value in data.items():
            if hasattr(value, 'isoformat'):
                serializable_data[key] = value.isoformat()
            else:
                serializable_data[key] = value
        self.redis.setex(redis_key, 3600, json.dumps(serializable_data))
        log.debug(f"Saved session to Redis: {redis_key}")

    @retry_redis
    def get(self, sid: str) -> dict | None:
        redis_key = f"analytics_session:{sid}"
        data = self.redis.get(redis_key)
        if data:
            log.debug(f"Retrieved session from Redis: {redis_key}")
            parsed_data = json.loads(data)  # type: ignore[arg-type]
            if 'timestamp' in parsed_data:
                parsed_data['timestamp'] = datetime.fromisoformat(parsed_data['timestamp'])
            return parsed_data
        log.debug(f"No session found in Redis: {redis_key}")
        return None

    @retry_redis
    def delete(self, sid: str) -> None:
        redis_key = f"analytics_session:{sid}"
        deleted = self.redis.delete(redis_key)
        if deleted:
            log.debug(f"Deleted session from Redis: {redis_key}")
