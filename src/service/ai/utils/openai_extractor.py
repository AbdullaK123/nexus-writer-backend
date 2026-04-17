import time
from typing import TypeVar, Generic, Type

from openai import (
    AsyncOpenAI,
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
)
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.infrastructure.config.settings import settings, config
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)

T = TypeVar("T", bound=BaseModel)


class RefusalError(Exception):
    """Raised when the model refuses to respond (safety filter, policy, etc.)."""

    def __init__(self, refusal: str, model: str, output_type: str):
        self.refusal = refusal
        self.model = model
        self.output_type = output_type
        super().__init__(f"Model {model} refused extraction for {output_type}: {refusal}")


def _before_sleep_openai(retry_state):
    """Log OpenAI retry attempts via loguru."""
    exception = retry_state.outcome.exception()
    log.warning(
        "openai.retry",
        attempt=retry_state.attempt_number,
        wait_s=round(getattr(retry_state.next_action, "sleep", 0), 2),
        error_type=type(exception).__name__,
        error=str(exception),
    )


class OpenAIExtractor(Generic[T]):
    """
    Generic structured extractor using OpenAI's Strict Mode.

    The schema is enforced at the API layer via constrained decoding,
    so malformed output is impossible by construction. The only non-parse
    failure path is a model refusal, which is raised as RefusalError.
    """

    def __init__(
        self,
        model: Type[T],
        system_prompt: str,
        openai_model: str | None = None,
        api_key: str | None = None,
    ):
        self._model = model
        self._system_prompt = system_prompt
        self._default_openai_model = openai_model or config.openai.model
        self._client = AsyncOpenAI(
            api_key=api_key or settings.openai_api_key,
        )

    @retry(
        retry=retry_if_exception_type(
            (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        before_sleep=_before_sleep_openai,
        reraise=True,
    )
    async def extract(self, text: str, openai_model: str | None = None) -> T:
        model_name = self._model.__name__
        openai_model = openai_model or self._default_openai_model
        log.debug(
            "openai.extract.start",
            model=openai_model,
            output_type=model_name,
            input_len=len(text),
        )
        t0 = time.perf_counter()
        try:
            response = await self._client.chat.completions.parse(
                model=openai_model,
                temperature=0,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": text},
                ],
                response_format=self._model,
            )
        except Exception:
            log.opt(exception=True).error(
                "openai.extract.error",
                model=openai_model,
                output_type=model_name,
                elapsed_s=round(time.perf_counter() - t0, 2),
            )
            raise

        message = response.choices[0].message

        if message.refusal:
            log.warning(
                "openai.extract.refusal",
                model=openai_model,
                output_type=model_name,
                refusal=message.refusal,
            )
            raise RefusalError(
                refusal=message.refusal,
                model=openai_model,
                output_type=model_name,
            )

        result = message.parsed
        if result is None:
            log.error(
                "openai.extract.empty_response",
                model=openai_model,
                output_type=model_name,
            )
            raise ValueError("OpenAI returned no parsed content and no refusal")

        elapsed = round(time.perf_counter() - t0, 2)
        usage = response.usage
        log.debug(
            "openai.extract.done",
            model=openai_model,
            output_type=model_name,
            elapsed_s=elapsed,
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
        )
        return result

    async def extract_many(
        self, texts: list[str], openai_model: str | None = None
    ) -> list[T]:
        import asyncio

        model_name = self._model.__name__
        resolved_model = openai_model or self._default_openai_model
        log.debug(
            "openai.extract_many.start",
            model=resolved_model,
            output_type=model_name,
            batch_size=len(texts),
        )
        t0 = time.perf_counter()
        results = await asyncio.gather(
            *[self.extract(t, openai_model=openai_model) for t in texts]
        )
        elapsed = round(time.perf_counter() - t0, 2)
        log.debug(
            "openai.extract_many.done",
            model=resolved_model,
            output_type=model_name,
            batch_size=len(texts),
            elapsed_s=elapsed,
        )
        return results