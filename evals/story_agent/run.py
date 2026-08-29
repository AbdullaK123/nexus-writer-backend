from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any, Literal

import logfire

from src.infrastructure.config import config, settings

from .dataset import build_dataset
from .red_team_dataset import build_red_team_dataset
from .runtime import StoryAgentRun, make_task

SuiteName = Literal["baseline", "red-team"]


def _print_case_responses(report: Any) -> None:
    print("\nMODEL RESPONSES")
    print("=" * 80)

    for case in report.cases:
        print(f"\nCASE: {case.name}")

        output = case.output
        if isinstance(output, StoryAgentRun):
            called_tools = ", ".join(output.called_tools) or "none"
            print(f"CALLED TOOLS: {called_tools}")
            print("ANSWER:")
            print(output.answer)
        else:
            print("OUTPUT:")
            print(output)

        failed_assertions = [
            name
            for name, result in case.assertions.items()
            if result.value is False
        ]
        if failed_assertions:
            print(f"FAILED: {', '.join(failed_assertions)}")

        print("-" * 80)


def _build_suite(suite: SuiteName, judge_model: str):
    if suite == "red-team":
        return build_red_team_dataset(judge_model)
    return build_dataset(judge_model)


async def run_suite(
    *,
    model: str,
    judge_model: str,
    max_concurrency: int,
    repeat: int,
    suite: SuiteName,
) -> None:
    os.environ["OPENROUTER_API_KEY"] = settings.open_router_api_key

    logfire.configure(
        service_name="nexus-story-agent-evals",
        environment=settings.env,
    )
    logfire.instrument_pydantic_ai()

    judge = f"openrouter:{judge_model}"
    report = await _build_suite(suite, judge).evaluate(
        make_task(model),
        name=f"story-agent:{suite}:{model}",
        max_concurrency=max_concurrency,
        repeat=repeat,
        metadata={
            "target_model": model,
            "judge_model": judge_model,
            "suite": suite,
        },
    )
    report.print()
    _print_case_responses(report)


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
        "--suite",
        choices=("baseline", "red-team"),
        default="baseline",
        help="Behavioral suite to execute.",
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
        help=(
            "Number of times to run every case. Use repeats for red-team runs; "
            "a safety property that passes once and fails intermittently is not green."
        ),
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
            suite=args.suite,
        )
    )


if __name__ == "__main__":
    main()
