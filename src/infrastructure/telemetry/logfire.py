# from opentelemetry import trace
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor
# from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# from opentelemetry.sdk.resources import Resource
from src.infrastructure.config import settings
import logfire


def init_tracing(service_name: str):

    logfire.configure(
        service_name=service_name,
        environment=settings.env
    )
    logfire.instrument_pydantic_ai()
    logfire.instrument_asyncpg()
    logfire.instrument_system_metrics(base='full')

    # resource = Resource(attributes={
    #     "service.name": service_name,
    #     "deployment.environment": settings.env
    # })

    # provider = TracerProvider(resource=resource)

    # otlp_exporter = OTLPSpanExporter(endpoint=settings.jaegar_url)

    # processor = BatchSpanProcessor(otlp_exporter)

    # provider.add_span_processor(processor)

    # trace.set_tracer_provider(provider)