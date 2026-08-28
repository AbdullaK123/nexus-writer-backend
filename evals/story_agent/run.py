from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from typing import cast

from pydantic_evals import Case, Dataset

from src.infrastructure.config import config

from .dataset import StoryAgentEvalInput, dataset
from .evaluators import BinaryBehaviorJudge, RequiredTools
from .runtime import make_task


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
