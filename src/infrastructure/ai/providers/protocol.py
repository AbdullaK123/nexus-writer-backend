from typing import Protocol
from pydantic import BaseModel


class AIProvider(Protocol):

    async def generate(self, system_prompt: str, text: str, max_tokens: int) -> str:
        ...

    async def extract[T: BaseModel](
        self,
        system_prompt: str,
        text: str,
        max_tokens: int,
        model: type[T]
    ) -> T:
        ...