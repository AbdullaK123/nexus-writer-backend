import json
from typing import TypeVar, Generic, Type

from httpx import ConnectError, ReadTimeout
from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.infrastructure.config.settings import settings, config

T = TypeVar("T", bound=BaseModel)


class LFMExtractor(Generic[T]):
    def __init__(
        self,
        model: Type[T],
        system_prompt: str,
        ollama_model: str | None = None,
        base_url: str | None = None,
    ):
        self._model = model
        self._system_prompt = self._build_system_prompt(system_prompt, model)
        self._ollama_model = ollama_model or config.ollama.model
        self._client = AsyncOpenAI(
            base_url=base_url or settings.ollama_base_url,
            api_key="ollama",
        )

    def _build_system_prompt(self, system_prompt: str, model: Type[T]) -> str:
        schema = json.dumps(model.model_json_schema(), indent=2)
        return f"{system_prompt}\n\nReturn ONLY valid JSON conforming to this schema:\n{schema}"

    @retry(
        retry=retry_if_exception_type((ConnectError, ReadTimeout)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def extract(self, text: str) -> T:
        response = await self._client.chat.completions.create(
            model=self._ollama_model,
            temperature=0,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": text},
            ],
        )
        raw = response.choices[0].message.content
        if raw is None:
            raise ValueError("LLM returned empty content")
        return self._model.model_validate_json(raw)

    async def extract_many(self, texts: list[str]) -> list[T]:
        import asyncio
        return await asyncio.gather(*[self.extract(t) for t in texts])
