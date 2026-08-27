from typing import Any


class FakeAIProvider:
    def __init__(self):
        self.generate_response: str = "Generated text"
        self.extract_response: Any = None
        self.extract_responses: dict[type, Any] = {}
        self.extract_calls: list[dict[str, Any]] = []
        self.embed_response: list[float] = [0.1] * 1536
        self.embed_many_response: list[list[float]] | None = None
        self.error: Exception | None = None
        self.call_count: int = 0
        self.model: str = "test-model"
        self.embedding_model: str = "test-embedding-model"

    async def generate(self, system_prompt: str, text: str, max_tokens: int) -> str:
        self.call_count += 1
        if self.error:
            raise self.error
        return self.generate_response

    async def extract(
        self,
        system_prompt: str,
        text: str,
        max_tokens: int,
        schema: type,
    ):
        self.call_count += 1
        self.extract_calls.append(
            {
                "system_prompt": system_prompt,
                "text": text,
                "max_tokens": max_tokens,
                "schema": schema,
            }
        )
        if self.error:
            raise self.error
        return self.extract_responses.get(schema, self.extract_response)

    async def embed(self, text: str) -> list[float]:
        self.call_count += 1
        if self.error:
            raise self.error
        return self.embed_response

    async def embed_many(
        self,
        texts: list[str],
        with_batching: bool = False,
    ) -> list[list[float]]:
        self.call_count += 1
        if self.error:
            raise self.error
        if self.embed_many_response:
            return self.embed_many_response
        return [self.embed_response for _ in texts]
