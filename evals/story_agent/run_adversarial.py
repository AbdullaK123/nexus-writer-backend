from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any

import logfire

from src.infrastructure.config import config, settings

from .adversarial_dataset import build_adversarial_dataset
from .run import _print_case_responses
from .runtime import make_task


async def run_suite(
    *,
    model: str,
    judge_model: str,
    max_concurrency: int,
    repeat: int,
) -> None:
    os.environ["OPENROUTER_API_KEY"] = settings.open_router_api_key

    logfire.configure(
        service_name="nexus-story-agent-adversarial-evals",
        environment=settings.env,
    )
    logfire.instrument_pydantic_ai()

    report = await build_adversarial_dataset(f"openrouter:{judge_model}").evaluate(
        make_task(model),
        name=f"story-agent-adversarial:{model}",
        max_concurrency=max_concurrency,
        repeat=repeat,
        metadata={
            "target_model": model,
            "judge_model": judge_model,
            "suite": "adversarial",
        },
    )
    report.print()
    _print_case_responses(report)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Nexus story-agent adversarial behavioral eval suite."
    )
    parser.add_argument("--model", default=config.ai.default_model)
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--max-concurrency", type=int, default=2)
    parser.add_argument(
        "--repeat",
        type=int,
        default=5,
        help="Adversarial cases default to repeated runs so flaky semantic failures are visible.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    asyncio.run(run_suite(
        model=args.model,
        judge_model=args.judge_model or args.model,
        max_concurrency=args.max_concurrency,
        repeat=args.repeat,
    ))


if __name__ == "__main__":
    main()
