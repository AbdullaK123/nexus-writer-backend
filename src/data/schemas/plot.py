from typing import List, Optional
from pydantic import BaseModel
from src.data.schemas.extraction import PlotThread, ThreadImportance, ThreadStatus


class PlotQuery(BaseModel):
    status: Optional[ThreadStatus] = None
    importance: Optional[ThreadImportance] = None
    tags: Optional[List[str]] = None
    search_term: Optional[str] = None


class PlotThreadListResponse(BaseModel):
    threads: Optional[List[PlotThread]] = []
    is_stale: Optional[bool] = False
    num_found: Optional[int] = 0