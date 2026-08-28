from __future__ import annotations

import argparse
import asyncio
from typing import Any

from src.infrastructure.config import config

from .dataset import build_dataset
from .runtime import StoryAgentRun, make_task


def _print_failed_cases(report: Any) -> None:
    failed_cases = [
        case
        for case in report.cases
        if any(result.value is False for result in case.assertions.values())
    ]

    if not failed_cases:
        return

    print("\nFAILED CASE DETAILS")
    print("=" * 80)

    for case in failed_cases:
        failed_assertions = [
            name
            for name, result in case.assertions.items()
            if result.value is False
        ]

        print(f"\nCASE: {case.name}")
        print(f"FAILED: {', '.join(failed_assertions)}")

        output = case.output
        if isinstance(output, StoryAgentRun):
            called_tools = ", ".join(output.called_tools) or "none"
            print(f"CALLED TOOLS: {called_tools}")
            print("ANSWER:")
            print(output.answer)
        else:
            print("OUTPUT:")
            print(output)

        print("-" * 80)


async def run_suite(
    *,
    model: str,
    judge_model: str,
    max_concurrency: int,
    repeat: int,
) -> None:
    report = await build_dataset(judge_model).evaluate(
        make_task(model),
        name=f"story-agent:{model}",
        max_concurrency=max_concurrency,
        repeat=repeat,
        metadata={
            "target_model": model,
            "judge_model": judge_model,
        },
    )
    report.print()
    _print_failed_cases(report)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Nexus story-agent behavioral eval suite."
    )
    parser.add_argument(
        "--model",
        default=config.ai.default_model,
        help="OpenRouter model name for the story agent.",
    )
    parser.add_argument(
        "--judge-model",
        default=None,
        help="Model name for the binary LLM judges. Defaults to --model.",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=2,
        help="Maximum number of cases evaluated concurrently.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of times to run every case.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    asyncio.run(
        run_suite(
            model=args.model,
            judge_model=args.judge_model or args.model,
            max_concurrency=args.max_concurrency,
            repeat=args.repeat,
        )
    )


if __name__ == "__main__":
    main()
