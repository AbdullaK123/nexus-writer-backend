from typing import List, Protocol
from pydantic import BaseModel


class AIProvider(Protocol):
    model: str
    embedding_model: str

    async def generate(self, system_prompt: str, text: str, max_tokens: int) -> str: ...

    async def extract[T: BaseModel](
        self, system_prompt: str, text: str, max_tokens: int, schema: type[T]
    ) -> T: ...

    async def embed(self, text: str) -> List[float]: ...
        
    async def embed_many(self, texts: List[str], with_batching: bool = False) -> List[List[float]]: ...