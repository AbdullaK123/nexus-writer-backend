from typing import Protocol, Union
from asyncio import Semaphore
from openai import AsyncOpenAI

class AIProvider(Protocol):

    model: str
    temperature: float
    _sem: Semaphore
    _client: Union[AsyncOpenAI] # we'll add more async clients later


    async def _generate(self, system_prompt: str, text: str, max_tokens: int) -> str:
        ...

    async def generate(self, system_prompt: str, text: str, max_tokens: int) -> str:
        ...
