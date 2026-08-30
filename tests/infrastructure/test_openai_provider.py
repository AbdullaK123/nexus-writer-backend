from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from src.infrastructure.ai.providers.openai import OpenAIProvider
from src.infrastructure.exceptions import LLMServiceError


class FakeCompletions:
    def __init__(self) -> None:
        self.create_response = None
        self.parse_response = None

    async def create(self, **kwargs):
        return self.create_response

    async def parse(self, **kwargs):
        return self.parse_response


def provider_with(client) -> OpenAIProvider:
    provider = object.__new__(OpenAIProvider)
    provider.model = "test-model"
    provider.embedding_model = "test-embedding"
    provider.embeddings_batch_size = 8
    provider.max_concurrent_requests = 2
    provider.temperature = 0.0
    provider._sem = asyncio.Semaphore(2)
    provider._client = client
    return provider


def completion_response(*, content: str | None, finish_reason: str = "stop"):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason=finish_reason,
                message=SimpleNamespace(content=content, parsed=content),
            )
        ],
        usage=None,
    )


@pytest.mark.asyncio
async def test_generate_rejects_truncated_provider_output() -> None:
    completions = FakeCompletions()
    completions.create_response = completion_response(
        content="partial",
        finish_reason="length",
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    provider = provider_with(client)

    with pytest.raises(LLMServiceError, match="max_completion_tokens"):
        await provider.generate("system", "input", 10)


@pytest.mark.asyncio
async def test_generate_rejects_success_response_without_content() -> None:
    completions = FakeCompletions()
    completions.create_response = completion_response(content=None)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    provider = provider_with(client)

    with pytest.raises(LLMServiceError, match="empty content"):
        await provider.generate("system", "input", 10)


@pytest.mark.asyncio
async def test_extract_rejects_success_response_without_parsed_schema() -> None:
    completions = FakeCompletions()
    completions.parse_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason="stop",
                message=SimpleNamespace(parsed=None),
            )
        ],
        usage=None,
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    provider = provider_with(client)

    class Output(BaseModel):
        value: str

    with pytest.raises(LLMServiceError, match="empty extraction"):
        await provider.extract("system", "input", 10, Output)


@pytest.mark.asyncio
async def test_batched_embeddings_preserve_input_order_when_later_batch_finishes_first() -> None:
    provider = provider_with(SimpleNamespace())
    provider.max_concurrent_requests = 2
    completion_order: list[str] = []

    async def fake_batch(texts: list[str]) -> list[list[float]]:
        first = texts[0]
        await asyncio.sleep(0 if first == "8" else 0.02)
        completion_order.append(first)
        return [[float(text)] for text in texts]

    provider._embed_many_raw = fake_batch  # type: ignore[method-assign]

    result = await provider._embed_many_batched([str(i) for i in range(12)])

    assert completion_order == ["8", "0"], (
        "the test must actually force later input to finish first or it proves nothing about gather-order safety"
    )
    assert result == [[float(i)] for i in range(12)], (
        "concurrent embedding batches must be flattened in input order or vectors become attached to the wrong scenes"
    )


@pytest.mark.asyncio
async def test_public_provider_semaphore_bounds_concurrent_generation() -> None:
    provider = provider_with(SimpleNamespace())
    active = 0
    max_active = 0

    async def fake_generate(system_prompt: str, text: str, max_tokens: int) -> str:
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        return text

    provider._generate = fake_generate  # type: ignore[method-assign]

    results = await asyncio.gather(
        *(provider.generate("system", str(i), 10) for i in range(8))
    )

    assert results == [str(i) for i in range(8)]
    assert max_active == 2, (
        "the concrete provider must enforce its concurrency budget or a burst can bypass backpressure and stampede the upstream model API"
    )
