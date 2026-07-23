from saq import Queue
from src.infrastructure.config.settings import settings as app_settings
import redis.asyncio as aioredis

client = aioredis.Redis.from_url(app_settings.redis_url, socket_timeout=None, socket_connect_timeout=5)

queue = Queue(client)