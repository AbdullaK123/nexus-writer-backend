"""
Prefect worker entry point for running flows in a separate container.

This worker processes flow runs from the Prefect server/cloud.
It should be run in a dedicated container separate from the API server.
"""
import asyncio
from prefect import aserve
from loguru import logger
from app.config.logging import setup_logging
from app.core.mongodb import MongoDB
from app.flows.extraction import extract_single_chapter_flow, reextract_chapters_flow
from app.flows.line_edits import line_edits_flow
from dotenv import load_dotenv
from app.config.settings import app_config

load_dotenv()
setup_logging()


async def main():
    """Start the Prefect worker serving all flows."""
    logger.info("Starting Prefect worker...")
    logger.info("Registering flows: extract_single_chapter, line_edits")
    
    # Serve all flows - this makes them available for execution
    # The worker will poll for flow runs and execute them
    await aserve(
        await extract_single_chapter_flow.to_deployment(
            name="chapter-extraction-deployment", 
            tags=["extraction", "chapter"],
        ),
        await line_edits_flow.to_deployment(
            name="line-edits-deployment",
            tags=["line-edits"],
        ),
        await reextract_chapters_flow(
            name="chapter-reextraction-deployment",
            tags=["reextraction", "extraction", "chapters"]
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
