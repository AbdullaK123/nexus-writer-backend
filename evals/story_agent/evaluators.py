from __future__ import annotations

from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class RequiredTools(Evaluator):
    required: tuple[str, ...]

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        called_tools = set(getattr(ctx.output, "called_tools", ()))
        return set(self.required).issubset(called_tools)
