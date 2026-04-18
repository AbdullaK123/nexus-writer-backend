from openai import AsyncOpenAI
from src.infrastructure.config import config, settings
from src.infrastructure.utils.decorators import handle_openai_errors
import asyncio


class OpenAIProvider:

    def __init__(
        self,
        model: str = config.ai.default_model,
        temperature: float = config.ai.temperature,
        max_concurrent_requests: int = config.ai.max_concurrent_requests
    ):
        self.model=model
        self.temperature=temperature
        self._sem = asyncio.Semaphore(max_concurrent_requests)
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            max_retries=config.ai.max_retries,
            timeout=config.ai.timeout
        )

    @handle_openai_errors
    async def _generate(self, system_prompt: str, text: str, max_tokens: int) -> str:
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            max_completion_tokens=max_tokens,
            temperature=self.temperature
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("Open AI Provider returned empty content")
        return content
    
    async def generate(self, system_prompt: str, text: str, max_tokens: int) -> str:
        async with self._sem:
            return await self._generate(
                system_prompt,
                text,
                max_tokens
            )