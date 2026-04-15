"""
Prefect worker entry point for running flows in a separate container.

This worker processes flow runs from the Prefect server/cloud.
It should be run in a dedicated container separate from the API server.
"""
import asyncio
from prefect import aserve
from src.shared.utils.logging_context import get_layer_logger, LAYER_APP
from src.infrastructure.config.logging import setup_logging
from src.service.flows.containers import FlowContainer
from src.service.flows.extraction import extract_single_chapter_flow, reextract_chapters_flow
from src.service.flows.line_edits import line_edits_flow
from dotenv import load_dotenv

load_dotenv()
setup_logging()

log = get_layer_logger(LAYER_APP)

flow_container = FlowContainer()


async def main():
    """Start the Prefect worker serving all flows."""
    log.info("worker.starting")

    await flow_container.init_resources()  # type: ignore[misc]
    log.info("worker.infra_ready")

    log.info("worker.registering_flows", flows=["extract_single_chapter", "line_edits"])
    
    # Serve all flows - this makes them available for execution
    # The worker will poll for flow runs and execute them
    try:
        await aserve(
            await extract_single_chapter_flow.to_deployment(
                name="chapter-extraction-deployment", 
                tags=["extraction", "chapter"],
            ),
            await line_edits_flow.to_deployment(
                name="line-edits-deployment",
                tags=["line-edits"],
            ),
            await reextract_chapters_flow.to_deployment(
                name="chapter-reextraction-deployment",
                tags=["reextraction", "extraction", "chapters"]
            )
        )
    finally:
        await flow_container.shutdown_resources()  # type: ignore[misc]


if __name__ == "__main__":
    asyncio.run(main())
