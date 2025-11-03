import hashlib
from typing import Optional
from app.agents.models import ChapterEdit
from app.agents.models.prose import ChapterEditResponse
from app.core.redis import get_redis
import json


class EditCache:

    def __init__(self):
        self.redis = get_redis()
        self.ttl = 60 * 60 * 24

    def _make_key(self, text: str, user_id: str) -> str:
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
        return f"edits:{user_id}:{text_hash}"

    def get(self, text: str, user_id: str) -> Optional[dict]:
        key = self._make_key(text, user_id)
        cached_edits = self.redis.get(key)
        if cached_edits:
            data = json.loads(cached_edits)
            return data
        return None

    def set(self, text: str, user_id: str, response: ChapterEditResponse):
        key = self._make_key(text, user_id)
        data = response.model_dump(exclude={'from_cache'})
        self.redis.set(key, json.dumps(data), ex=self.ttl)

    def invalidate(self, text: str, user_id: str):
        key = self._make_key(text, user_id)
        self.redis.delete(key)