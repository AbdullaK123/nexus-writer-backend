from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from typing import Any, cast

from pydantic_evals import Case, Dataset

from src.infrastructure.config import config

from .dataset import StoryAgentEvalInput, dataset
from .evaluators import BinaryBehaviorJudge, RequiredTools
from .runtime import StoryAgentRun, make_task


Metadata = dict[str, str]


def build_eval_dataset(judge_model: str) -> Dataset[StoryAgentEvalInput, object, Metadata]:
    cases = cast(
        Sequence[Case[StoryAgentEvalInput, object, Metadata]],
        dataset.cases,
    )
    return Dataset(
        name=dataset.name,
        cases=cases,
        evaluators=[
            RequiredTools(),
            BinaryBehaviorJudge(model_name=judge_model),
        ],
    )


def _print_failed_cases(report: Any) -> None:
    failed_cases = [
        case
        for case in report.cases
        if any(passed is False for passed in case.assertions.values())
    ]

    if not failed_cases:
        return

    print("\nFAILED CASE DETAILS")
    print("=" * 80)

    for case in failed_cases:
        failed_assertions = [
            name
            for name, passed in case.assertions.items()
            if passed is False
        ]

        print(f"\nCASE: {case.name}")
        print(f"FAILED: {', '.join(failed_assertions)}")

        expected = case.expected_output
        if expected is not None:
            behavior = getattr(expected, "behavior", None)
            rationale = getattr(expected, "rationale", None)
            if behavior:
                print(f"EXPECTED BEHAVIOR: {behavior}")
            if rationale:
                print(f"RATIONALE: {rationale}")

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
    eval_dataset = build_eval_dataset(judge_model)
    report = await eval_dataset.evaluate(
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
        help="OpenRouter model name for the binary yes/no judge. Defaults to --model.",
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
