from typing import Optional

from pydantic import BaseModel
from src.data.schemas.extraction import VoiceProfile


class VoiceProfileResponse(BaseModel):
    voice_profile: Optional[VoiceProfile] = None
    is_stale: Optional[bool] = False