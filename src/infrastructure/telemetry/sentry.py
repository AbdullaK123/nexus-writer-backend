import sentry_sdk
from src.infrastructure.config import settings, config


def init_sentry(service_name: str) -> None:
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        traces_sample_rate=config.sentry.traces_sample_rate,
        send_default_pii=False,
    )

    sentry_sdk.set_tag("service", service_name)