from openai import AsyncOpenAI
from pydantic import BaseModel
from src.infrastructure.config import config, settings
from src.infrastructure.utils.decorators import handle_openai_errors
import asyncio
from loguru import logger



class OpenAIProvider:
    def __init__(
        self,
        model: str = config.ai.default_model,
        temperature: float = config.ai.temperature,
        max_concurrent_requests: int = config.ai.max_concurrent_requests,
    ):
        self.model = model
        self.temperature = temperature
        self._sem = asyncio.Semaphore(max_concurrent_requests)
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            max_retries=config.ai.max_retries,
            timeout=config.ai.timeout,
        )

    @handle_openai_errors
    async def _generate(self, system_prompt: str, text: str, max_tokens: int) -> str:
        logger.info("openai.generate.start", model=self.model, max_tokens=max_tokens)
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            max_completion_tokens=max_tokens,
            temperature=self.temperature,
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("Open AI Provider returned empty content")
        usage = response.usage
        logger.info(
            "openai.generate.done",
            model=self.model,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
        )
        return content

    @handle_openai_errors
    async def _extract[T: BaseModel](
        self, system_prompt: str, text: str, max_tokens: int, schema: type[T]
    ) -> T:
        logger.info("openai.extract.start", model=self.model, max_tokens=max_tokens, schema=schema.__name__)
        response = await self._client.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            response_format=schema,
            max_completion_tokens=max_tokens,
            temperature=self.temperature,
        )
        content = response.choices[0].message.parsed
        if content is None:
            raise ValueError("Open AI Provider returned empty extraction")
        usage = response.usage
        logger.info(
            "openai.extract.done",
            model=self.model,
            schema=schema.__name__,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
        )
        return content

    async def generate(self, system_prompt: str, text: str, max_tokens: int) -> str:
        async with self._sem:
            return await self._generate(system_prompt, text, max_tokens)

    async def extract[T: BaseModel](
        self, system_prompt: str, text: str, max_tokens: int, schema: type[T]
    ) -> T:
        async with self._sem:
            return await self._extract(system_prompt, text, max_tokens, schema)
