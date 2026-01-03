"""
Prefect worker entry point for running flows in a separate container.

This worker processes flow runs from the Prefect server/cloud.
It should be run in a dedicated container separate from the API server.
"""
import asyncio
from prefect import serve
from loguru import logger
from app.config.logging import setup_logging
from app.flows.extraction import cascade_extraction_flow, extract_single_chapter_flow
from app.flows.line_edits import line_edits_flow
from dotenv import load_dotenv


load_dotenv()
setup_logging()


def main():
    """Start the Prefect worker serving all flows."""
    logger.info("Starting Prefect worker...")
    logger.info("Registering flows: cascade_extraction, extract_single_chapter, line_edits")
    
    # Serve all flows - this makes them available for execution
    # The worker will poll for flow runs and execute them
    serve(
        extract_single_chapter_flow.to_deployment(
            name="chapter-extraction-deployment", 
            tags=["extraction", "chapter"],
        ),
        line_edits_flow.to_deployment(
            name="line-edits-deployment",
            tags=["line-edits"],
        ),
    )


if __name__ == "__main__":
    main()
