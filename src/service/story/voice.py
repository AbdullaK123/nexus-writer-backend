from src.data.schemas.extraction import VoiceProfile
from src.data.schemas.voice import VoiceProfileResponse
from src.data.models import Story, Extraction
from src.infrastructure.ai.enums import JobType
from src.service.exceptions import NotFoundError



async def get_voice_profile(story_id: str) -> VoiceProfileResponse:

    story_exists = await Story.filter(id=story_id).exists()

    if not story_exists:
        raise NotFoundError("Story not found")
    
    voice_profile_raw = await (
        Extraction
            .filter(story_id=story_id, type=JobType.VOICE.value)
            .only("is_stale", "data")
            .order_by("-created_at")
            .limit(1)
            .first()
    )

    if voice_profile_raw is None:
        raise NotFoundError("Voice profile not found")

    return VoiceProfileResponse(
        voice_profile=VoiceProfile(**voice_profile_raw.data),
        is_stale=voice_profile_raw.is_stale
    )
    
