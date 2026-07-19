from src.infrastructure.config import settings
import logfire


def init_tracing(service_name: str):

    logfire.configure(
        service_name=service_name,
        environment=settings.env
    )
    logfire.instrument_pydantic_ai()
    logfire.instrument_asyncpg()
    logfire.instrument_redis(capture_statement=True)
    logfire.instrument_system_metrics(base='full')