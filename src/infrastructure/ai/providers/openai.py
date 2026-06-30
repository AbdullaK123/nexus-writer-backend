from typing import List
from openai import AsyncOpenAI
from pydantic import BaseModel
from src.infrastructure.config import config, settings
from src.infrastructure.utils.decorators import handle_openai_errors
import asyncio
from itertools import batched, chain
from loguru import logger
import math



class OpenAIProvider:
    def __init__(
        self,
        model: str = config.ai.default_model,
        embedding_model: str = config.ai.embedding_model,
        temperature: float = config.ai.temperature,
        max_concurrent_requests: int = config.ai.max_concurrent_requests,
        embeddings_batch_size: int = config.ai.embedding_batch_size
    ):
        self.model = model
        self.embedding_model = embedding_model
        self.embeddings_batch_size = embeddings_batch_size
        self.max_concurrent_requests = max_concurrent_requests
        self.temperature = temperature
        self._sem = asyncio.Semaphore(max_concurrent_requests)
        self._client = AsyncOpenAI(
            base_url=settings.open_router_api_url,
            api_key=settings.open_router_api_key,
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
        if response.choices[0].finish_reason == "length":
            raise ValueError("OpenAI hit max_completion_tokens before producing output")
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
    async def _embed(self, text: str) -> List[float]:
        logger.info("openai.embed.start", model=self.embedding_model, count=1)
        response = await self._client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        data = response.data
        if data is None:
            raise ValueError("Open AI Provider failed to return embeddings")
        usage = response.usage
        logger.info(
            "openai.embed.done",
            model=self.embedding_model,
            count=1,
            prompt_tokens=usage.prompt_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
        )
        embedding = data[0].embedding
        return embedding
    
    @handle_openai_errors
    async def _embed_many(self, texts: List[str]) -> List[List[float]]:
        count = len(texts)
        logger.info("openai.embed_many.start", model=self.embedding_model, count=count)
        response = await self._client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )
        data = response.data
        if data is None:
            raise ValueError("Open AI Provider failed to return embeddings")
        usage = response.usage
        logger.info(
            "openai.embed_many.done",
            model=self.embedding_model,
            count=count,
            prompt_tokens=usage.prompt_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
        )
        return [
            e.embedding
            for e in data
        ]
    
    # Floor on batch size so small drains don't degenerate into one-text-per-call.
    # Without it, batch_size = ceil(total / max_concurrent) collapses to 1 whenever
    # total < max_concurrent (e.g. 18 scenes / 35 concurrency → 18 single-text HTTP calls).
    _MIN_EMBED_BATCH_SIZE = 8

    async def _embed_many_batched(self, texts: List[str]) -> List[List[float]]:
        total_count = len(texts)
        if total_count == 0:
            return []
        batch_size = min(
            max(
                math.ceil(total_count / self.max_concurrent_requests),
                self._MIN_EMBED_BATCH_SIZE,
            ),
            2048,
        )
        num_batches = math.ceil(total_count / batch_size)
        logger.info(
            "openai.embed_many_batched.start",
            model=self.embedding_model,
            total_count=total_count,
            batch_size=batch_size,
            num_batches=num_batches,
        )
        batched_texts = batched(texts, batch_size)
        result = await asyncio.gather(
            *(self._embed_many(batch) for batch in batched_texts)
        )
        embeddings = list(chain.from_iterable(result))
        logger.info(
            "openai.embed_many_batched.done",
            model=self.embedding_model,
            total_count=total_count,
            num_batches=num_batches,
        )
        return embeddings
        
        
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
            temperature=self.temperature
        )
        content = response.choices[0].message.parsed
        if response.choices[0].finish_reason == "length":
            raise ValueError("OpenAI hit max_completion_tokens before producing output")
        if content is None:
            raise ValueError("Open AI Provider returned empty extraction")
        usage = response.usage
        logger.info(
            "openai.extract.done",
            model=self.model,
            schema=schema.__name__,
            finish_reason=response.choices[0].finish_reason,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            reasoning_tokens=(
                usage.completion_tokens_details.reasoning_tokens
                if usage and usage.completion_tokens_details else None
            ),
        )
        return content

    async def generate(self, system_prompt: str, text: str, max_tokens: int) -> str:
        async with self._sem:
            return await self._generate(system_prompt, text, max_tokens)
        
    async def embed(self, text: str) -> List[float]:
        async with self._sem:
            return await self._embed(text)
        
    async def embed_many(self, texts: List[str], with_batching=False) -> List[List[float]]:
       async with self._sem:
           if with_batching:
               return await self._embed_many_batched(texts)
           else:
               return await self._embed_many(texts)

    async def extract[T: BaseModel](
        self, system_prompt: str, text: str, max_tokens: int, schema: type[T]
    ) -> T:
        async with self._sem:
            return await self._extract(system_prompt, text, max_tokens, schema)
