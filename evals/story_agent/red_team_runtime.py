from __future__ import annotations

from pydantic_ai import ModelRequest, ModelResponse
from pydantic_ai.messages import TextPart, UserPromptPart

from src.service.chat.agent import build_agent

from .runtime import StoryAgentRun, _extract_called_tools, make_deps


def make_red_team_task(model_name: str):
    agent = build_agent(model_name)

    async def run_story_agent(inputs) -> StoryAgentRun:
        history = []
        for turn in getattr(inputs, "prior_turns", ()):
            history.extend(
                [
                    ModelRequest(parts=[UserPromptPart(content=turn.user_message)]),
                    ModelResponse(parts=[TextPart(content=turn.assistant_message)]),
                ]
            )

        result = await agent.run(
            inputs.user_message,
            deps=make_deps(inputs),
            message_history=history,
        )
        return StoryAgentRun(
            answer=result.output,
            called_tools=_extract_called_tools(result.all_messages()),  # type: ignore[arg-type]
        )

    return run_story_agent
