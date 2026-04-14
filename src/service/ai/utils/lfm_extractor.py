import json
import time
from typing import TypeVar, Generic, Type

from httpx import ConnectError, ReadTimeout
from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.infrastructure.config.settings import settings, config
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)

T = TypeVar("T", bound=BaseModel)


def _before_sleep_lfm(retry_state):
    """Log LFM retry attempts via loguru."""
    exception = retry_state.outcome.exception()
    log.warning(
        "lfm.retry",
        attempt=retry_state.attempt_number,
        wait_s=round(getattr(retry_state.next_action, "sleep", 0), 2),
        error_type=type(exception).__name__,
        error=str(exception),
    )


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
        before_sleep=_before_sleep_lfm,
        reraise=True,
    )
    async def extract(self, text: str) -> T:
        model_name = self._model.__name__
        log.debug("lfm.extract.start", model=self._ollama_model, output_type=model_name, input_len=len(text))
        t0 = time.perf_counter()
        try:
            response = await self._client.chat.completions.create(
                model=self._ollama_model,
                temperature=0,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": text},
                ],
            )
        except Exception:
            log.opt(exception=True).error(
                "lfm.extract.error", model=self._ollama_model, output_type=model_name,
                elapsed_s=round(time.perf_counter() - t0, 2),
            )
            raise
        raw = response.choices[0].message.content
        if raw is None:
            log.error("lfm.extract.empty_response", model=self._ollama_model, output_type=model_name)
            raise ValueError("LLM returned empty content")
        try:
            result = self._model.model_validate_json(raw)
        except Exception:
            log.opt(exception=True).error(
                "lfm.extract.parse_error", model=self._ollama_model, output_type=model_name,
                response_len=len(raw),
            )
            raise
        elapsed = round(time.perf_counter() - t0, 2)
        usage = response.usage
        log.debug(
            "lfm.extract.done", model=self._ollama_model, output_type=model_name,
            elapsed_s=elapsed, response_len=len(raw),
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
        )
        return result

    async def extract_many(self, texts: list[str]) -> list[T]:
        import asyncio
        model_name = self._model.__name__
        log.debug("lfm.extract_many.start", model=self._ollama_model, output_type=model_name, batch_size=len(texts))
        t0 = time.perf_counter()
        results = await asyncio.gather(*[self.extract(t) for t in texts])
        elapsed = round(time.perf_counter() - t0, 2)
        log.debug("lfm.extract_many.done", model=self._ollama_model, output_type=model_name, batch_size=len(texts), elapsed_s=elapsed)
        return results
