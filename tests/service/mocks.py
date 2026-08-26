# tests/service/mocks.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Sequence
from uuid_extensions import uuid7str

from src.data.schemas.auth import UserRow, SessionRow
from src.data.schemas.story import StoryRow
from src.data.schemas.chapter import ChapterRow
from src.data.schemas.scene import SceneRow, SceneSearchResult
from src.data.schemas.enums import StoryStatus

class FakeQueue:
    def __init__(self):
        self.enqueued: list[tuple[str, dict]] = []
        self.error: Exception | None = None

    async def enqueue(self, job_name: str, **kwargs):
        if self.error:
            raise self.error
        self.enqueued.append((job_name, kwargs))

class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class FakeConnection:
    def transaction(self):
        return FakeTransaction()


class FakePool:
    def acquire(self):
        return FakePoolContext()


class FakePoolContext:
    async def __aenter__(self):
        return FakeConnection()

    async def __aexit__(self, *args):
        pass


# ── helpers ───────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Fake Redis (cache) ───────────────────────────────

class FakeRedis:

    def __init__(self):
        self._store: dict[str, Any] = {}

    async def get(self, key: str) -> Any | None:
        return self._store.get(key)

    async def set(self, key: str, value: Any, *, ex: int | None = None, nx: bool = False) -> bool | None:
        if nx and key in self._store:
            return None
        self._store[key] = value
        return True

    async def delete(self, *keys: str) -> int:
        count = 0
        for key in keys:
            if key in self._store:
                del self._store[key]
                count += 1
        return count

    async def flush(self):
        self._store.clear()

    async def keys(self, pattern: str = "*") -> list[str]:
        prefix = pattern.rstrip("*")
        return [k for k in self._store if k.startswith(prefix)]

    def poison(self, key: str, value: Any):
        """Inject corrupt data for cache poisoning tests."""
        self._store[key] = value


# ── Fake PubSub ──────────────────────────────────────

class FakePubSub:

    def __init__(self):
        self.published: list[tuple[str, object]] = []
        self.error: Exception | None = None

    async def publish(self, channel: str, payload: object) -> None:
        if self.error:
            raise self.error
        self.published.append((channel, payload))


# ── Fake AI Provider ─────────────────────────────────

class FakeAIProvider:

    def __init__(self):
        self.generate_response: str = "Generated text"
        self.extract_response: Any = None
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

    async def extract(self, system_prompt: str, text: str, max_tokens: int, schema: type):
        self.call_count += 1
        if self.error:
            raise self.error
        return self.extract_response

    async def embed(self, text: str) -> list[float]:
        self.call_count += 1
        if self.error:
            raise self.error
        return self.embed_response

    async def embed_many(self, texts: list[str], with_batching: bool = False) -> list[list[float]]:
        self.call_count += 1
        if self.error:
            raise self.error
        if self.embed_many_response:
            return self.embed_many_response
        return [self.embed_response for _ in texts]


# ── Fake User Repository ─────────────────────────────

class FakeUserRepository:

    def __init__(self):
        self._users: dict[str, UserRow] = {}
        self._by_email: dict[str, str] = {}
        self.error: Exception | None = None

    def seed(self, user: UserRow):
        self._users[user.id] = user
        self._by_email[user.email] = user.id

    async def get_by_id(self, user_id: str) -> UserRow | None:
        if self.error: raise self.error
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> UserRow | None:
        if self.error: raise self.error
        uid = self._by_email.get(email)
        return self._users.get(uid) if uid else None

    async def create(self, *, username: str, email: str, password_hash: str, profile_img: str | None) -> UserRow:
        if self.error: raise self.error
        user = UserRow(
            id=uuid7str(), username=username, email=email,
            password_hash=password_hash, profile_img=profile_img,
            settings={}, created_at=_now(), updated_at=_now(),
        )
        self.seed(user)
        return user

    async def update_settings(self, user_id: str, update: dict) -> UserRow | None:
        if self.error: raise self.error
        user = self._users.get(user_id)
        if not user: return None
        merged = {**user.settings, **update}
        updated = user.model_copy(update={"settings": merged, "updated_at": _now()})
        self._users[user_id] = updated
        return updated

    async def get_dashboard(self, *, user_id: str) -> tuple[dict, list[dict]]:
        if self.error: raise self.error
        return {}, []

    async def get_editor_link_params(self, *, user_id: str) -> list[tuple]:
        if self.error: raise self.error
        return []

    async def get_chat_link_params(self, *, user_id: str) -> list[tuple]:
        if self.error: raise self.error
        return []


# ── Fake Session Repository ──────────────────────────

class FakeSessionRepository:

    def __init__(self):
        self._sessions: dict[str, SessionRow] = {}
        self.error: Exception | None = None

    def seed(self, session: SessionRow):
        self._sessions[session.session_id] = session

    async def get(self, session_id: str) -> SessionRow | None:
        if self.error: raise self.error
        return self._sessions.get(session_id)

    async def create(self, *, user_id: str, session_id: str, expires_at: datetime,
                     ip_address: str | None = None, user_agent: str | None = None) -> SessionRow:
        if self.error: raise self.error
        session = SessionRow(
            session_id=session_id, user_id=user_id, expires_at=expires_at,
            ip_address=ip_address, user_agent=user_agent,
            created_at=_now(), updated_at=_now(),
        )
        self.seed(session)
        return session

    async def delete(self, session_id: str) -> bool:
        if self.error: raise self.error
        return self._sessions.pop(session_id, None) is not None

    async def delete_expired(self) -> int:
        if self.error: raise self.error
        now = _now()
        expired = [k for k, v in self._sessions.items() if v.expires_at < now]
        for k in expired:
            del self._sessions[k]
        return len(expired)


# ── Fake Story Repository ────────────────────────────

class FakeStoryRepository:

    def __init__(self):
        self._stories: dict[str, StoryRow] = {}
        self._path_arrays: dict[str, list[str]] = {}
        self.error: Exception | None = None
        self.force_update_none: bool = False

    def seed(self, story: StoryRow):
        self._stories[story.id] = story
        self._path_arrays[story.id] = list(story.path_array or [])

    async def get(self, story_id: str, user_id: str, *, executor=None) -> StoryRow | None:
        if self.error: raise self.error
        story = self._stories.get(story_id)
        if story and story.user_id == user_id:
            return story
        return None

    async def list_for_user(self, user_id: str) -> list[StoryRow]:
        if self.error: raise self.error
        return [s for s in self._stories.values() if s.user_id == user_id]

    async def exists_with_title(self, user_id: str, title: str) -> bool:
        if self.error: raise self.error
        return any(s.user_id == user_id and s.title == title for s in self._stories.values())

    async def create(self, *, user_id: str, title: str) -> StoryRow:
        if self.error: raise self.error
        story = StoryRow(
            id=uuid7str(), user_id=user_id, title=title,
            story_context=None, status=StoryStatus.ONGOING,
            path_array=[], created_at=_now(), updated_at=_now(),
        )
        self.seed(story)
        return story

    async def update(self, *, story_id: str, user_id: str, fields: dict) -> StoryRow | None:
        if self.error: raise self.error
        if self.force_update_none: return None
        story = await self.get(story_id, user_id)
        if not story: return None
        updated = story.model_copy(update={**fields, "updated_at": _now()})
        self._stories[story_id] = updated
        return updated

    async def delete(self, *, story_id: str, user_id: str) -> bool:
        if self.error: raise self.error
        story = self._stories.get(story_id)
        if story and story.user_id == user_id:
            del self._stories[story_id]
            return True
        return False

    async def set_path_array(self, story_id: str, path: Sequence[str], *, executor=None) -> None:
        if self.error: raise self.error
        self._path_arrays[story_id] = list(path)

    async def get_path_array(self, story_id: str, *, executor=None) -> list[str] | None:
        if self.error: raise self.error
        if story_id not in self._stories: return None
        return self._path_arrays.get(story_id, [])

    async def touch(self, story_id: str, *, executor=None) -> None:
        if self.error: raise self.error

    async def get_stats(self, story_id: str, user_id: str, *, executor=None) -> dict:
        if self.error: raise self.error
        return {}


# ── Fake Chapter Repository ──────────────────────────

class FakeChapterRepository:

    def __init__(self):
        self._chapters: dict[str, ChapterRow] = {}
        self.error: Exception | None = None
        self.force_return_none: bool = False
        self.pool = FakePool()

    def seed(self, chapter: ChapterRow):
        self._chapters[chapter.id] = chapter

    async def get(self, chapter_id: str, user_id: str, *, executor=None) -> ChapterRow | None:
        if self.error: raise self.error
        ch = self._chapters.get(chapter_id)
        if ch and ch.user_id == user_id:
            return ch
        return None

    async def get_for_system(self, chapter_id: str) -> ChapterRow | None:
        if self.error: raise self.error
        return self._chapters.get(chapter_id)

    async def get_with_story_title(self, chapter_id: str, user_id: str) -> tuple[ChapterRow, str, int] | None:
        if self.error: raise self.error
        ch = await self.get(chapter_id, user_id)
        if not ch: return None
        return ch, "Test Story", 1

    async def list_by_story(self, story_id: str, user_id: str, *, executor=None) -> list[ChapterRow]:
        if self.error: raise self.error
        return [c for c in self._chapters.values() if c.story_id == story_id and c.user_id == user_id]

    async def list_by_ids(self, chapter_ids: list[str], *, executor=None) -> list[ChapterRow]:
        if self.error: raise self.error
        return [self._chapters[cid] for cid in chapter_ids if cid in self._chapters]

    async def list_by_story_ids(self, story_ids: list[str], *, executor=None) -> list[ChapterRow]:
        if self.error: raise self.error
        return [c for c in self._chapters.values() if c.story_id in story_ids]

    async def create(self, *, story_id: str, user_id: str, title: str, content: str, word_count: int) -> ChapterRow:
        if self.error: raise self.error
        ch = ChapterRow(
            id=uuid7str(), story_id=story_id, user_id=user_id,
            title=title, content=content, published=False,
            word_count=word_count, next_chapter_id=None, prev_chapter_id=None,
            scenes_need_reextraction=False, scenes_extracted_at=None,
            created_at=_now(), updated_at=_now(),
        )
        self.seed(ch)
        return ch

    async def update(self, *, chapter_id: str, user_id: str, fields: dict, executor=None) -> ChapterRow | None:
        if self.error: raise self.error
        if self.force_return_none: return None
        ch = await self.get(chapter_id, user_id)
        if not ch: return None
        updated = ch.model_copy(update={**fields, "updated_at": _now()})
        self._chapters[chapter_id] = updated
        return updated

    async def delete(self, *, chapter_id: str, user_id: str, executor=None) -> ChapterRow | None:
        if self.error: raise self.error
        ch = self._chapters.get(chapter_id)
        if ch and ch.user_id == user_id:
            del self._chapters[chapter_id]
            return ch
        return None

    async def sync_pointers(self, path: Sequence[str], *, executor=None) -> None:
        if self.error: raise self.error

    async def mark_schapter_stale(
        self,
        chapter_id: str,
        *,
        executor=None
    ) -> None:
        if self.error: raise self.error
        ch = self._chapters.get(chapter_id)
        if not ch: return None
        updated = ch.model_copy(update={"scenes_need_reextraction": True})
        self._chapters[chapter_id] = updated

    async def mark_chapter_extracted(
        self,
        chapter_id: str,
        *,
        executor=None
    ) -> None:
        if self.error: raise self.error
        ch = self._chapters.get(chapter_id)
        if not ch: return None
        updated = ch.model_copy(update={"scenes_extracted_at": _now()})
        self._chapters[chapter_id] = updated

    async def list_stale_chapter_ids(
        self,
        *,
        window_seconds: int,
        limit: int,
        executor = None
    ) -> tuple[list[str], str]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        results = [ch for ch in self._chapters.values() if ch.scenes_need_reextraction and ch.updated_at <= cutoff and ch.published]
        return [ch.id for ch in results], results[0].user_id
        


# ── Fake Scene Repository ────────────────────────────

class FakeSceneRepository:

    def __init__(self, chapter_repo: FakeChapterRepository):
        self._scenes: dict[str, SceneRow] = {}
        self._chapter_repo = chapter_repo
        self.error: Exception | None = None
        self.pool: FakePool = FakePool()

    def seed(self, scene: SceneRow):
        self._scenes[scene.id] = scene

    async def list_by_chapter(self, chapter_id: str, *, executor=None) -> list[SceneRow]:
        if self.error: raise self.error
        return [s for s in self._scenes.values() if s.chapter_id == chapter_id]

    async def list_by_story(self, story_id: str, user_id: str, chapter_id: str | None = None, *, executor=None) -> list[SceneRow]:
        if self.error: raise self.error
        results = [s for s in self._scenes.values() if s.story_id == story_id and s.user_id == user_id]
        if chapter_id:
            results = [s for s in results if s.chapter_id == chapter_id]
        return results

    async def get_scene_text(self, scene_id: str, *, executor=None) -> str | None:
        if self.error: raise self.error
        scene = self._scenes.get(scene_id)
        return scene.description if scene else None

    async def get_scene_word_count(self, scene_id: str, *, executor=None) -> int:
        if self.error: raise self.error
        return 100

    async def replace_for_chapter(self, *, chapter_id: str, story_id: str, user_id: str, scenes: list, executor=None) -> list:
        if self.error: raise self.error
        # remove old scenes for this chapter
        self._scenes = {k: v for k, v in self._scenes.items() if v.chapter_id != chapter_id}
        return scenes

    async def update_embedding(self, scene_id: str, embedding: list[float], model: str, *, executor=None) -> None:
        if self.error: raise self.error

    async def list_pending_embeddings(self, chapter_id: str, *, executor=None) -> list[SceneRow]:
        if self.error: raise self.error
        return [s for s in self._scenes.values()
                if s.chapter_id == chapter_id and s.embedded_at is None]

    async def mark_chapter_stale(self, chapter_id: str, *, executor=None) -> None:
        if self.error: raise self.error
        chapter = self._chapter_repo._chapters.get(chapter_id)
        if chapter is None:
            return
        chapter.scenes_need_reextraction = True
        chapter.updated_at = _now()

    async def mark_chapter_extracted(self, chapter_id: str, *, executor=None) -> None:
        if self.error: raise self.error
        chapter = self._chapter_repo._chapters.get(chapter_id)
        if chapter is None:
            return
        now = _now()
        chapter.scenes_need_reextraction = False
        chapter.scenes_extracted_at = now
        chapter.updated_at = now

    async def list_stale_chapter_ids(self, story_id: str, *, executor=None) -> tuple[list[str], str]:
        if self.error: raise self.error
        return [], ""

    async def search_scenes(self, user_id: str, story_id: str, query_text: str,
                            k: int, candidate_pool: int, query_embedding: list[float],
                            **filters) -> list[SceneSearchResult]:
        if self.error: raise self.error
        return []

    async def list_story_tags(self, *, user_id: str, story_id: str, executor=None) -> list[dict]:
        if self.error: raise self.error
        return []

    async def list_story_entities(self, *, user_id: str, story_id: str, executor=None) -> list[dict]:
        if self.error: raise self.error
        return []

    async def list_povs(self, *, user_id: str, story_id: str, executor=None) -> list[dict]:
        if self.error: raise self.error
        return []


# ── Fake Analytics Repository ────────────────────────

class FakeAnalyticsRepository:

    def __init__(self):
        self.error: Exception | None = None

    async def get_cast_statistics(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error: raise self.error
        return []

    async def get_character_co_occurence_statistics(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error: raise self.error
        return []

    async def get_character_statistics(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error: raise self.error
        return []

    async def get_scene_length_distribution(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error: raise self.error
        return []

    async def get_tension_and_pacing_curves(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error: raise self.error
        return []

    async def get_recent_chapters_rythm(self, story_id: str, user_id: str, k: int = 5, *, executor=None) -> list:
        if self.error: raise self.error
        return []

    async def get_entity_statistics(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error: raise self.error
        return []

    async def get_questions_raised_by_chapter(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error: raise self.error
        return []


# ── Fake Chat Repository ─────────────────────────────

class FakeChatRepository:

    def __init__(self):
        self._threads: dict[str, dict] = {}
        self._messages: dict[str, list[dict]] = {}
        self.error: Exception | None = None

    async def create_thread(self, *, thread_id: str, user_id: str, story_id: str, title: str) -> dict:
        if self.error: raise self.error
        thread = {"id": thread_id, "user_id": user_id, "story_id": story_id, "title": title}
        self._threads[thread_id] = thread
        self._messages[thread_id] = []
        return thread

    async def get_thread(self, thread_id: str, user_id: str) -> dict | None:
        if self.error: raise self.error
        thread = self._threads.get(thread_id)
        if thread and thread["user_id"] == user_id:
            return thread
        return None

    async def list_threads_for_story(self, story_id: str, user_id: str) -> list[dict]:
        if self.error: raise self.error
        return [t for t in self._threads.values() if t["story_id"] == story_id and t["user_id"] == user_id]

    async def update_thread_title(self, thread_id: str, user_id: str, title: str) -> dict | None:
        if self.error: raise self.error
        thread = await self.get_thread(thread_id, user_id)
        if thread:
            thread["title"] = title
        return thread

    async def touch_thread(self, thread_id: str) -> None:
        if self.error: raise self.error

    async def delete_thread(self, thread_id: str, user_id: str) -> bool:
        if self.error: raise self.error
        thread = self._threads.get(thread_id)
        if thread and thread["user_id"] == user_id:
            del self._threads[thread_id]
            return True
        return False

    async def append_message(self, **kwargs) -> dict:
        if self.error: raise self.error
        thread_id = kwargs.get("thread_id", "")
        msg = kwargs
        if thread_id in self._messages:
            self._messages[thread_id].append(msg)
        return msg

    async def list_messages(self, thread_id: str, user_id: str) -> list[dict]:
        if self.error: raise self.error
        return self._messages.get(thread_id, [])