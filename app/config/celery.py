from celery import Celery
from app.config.settings import app_config

celery_app = Celery(
    "ai_workflows",
    broker=app_config.rabbitmq_url,
    backend=app_config.redis_url
)


