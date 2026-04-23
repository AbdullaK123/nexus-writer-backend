from typing import List
from pydantic import BaseModel


class ItemWithCount(BaseModel):
    value: str
    count: int

class ItemListResponse(BaseModel):
    items: List[ItemWithCount]