import asyncio

import asyncpg

from src.data.repositories.auth_tokens import AuthTokenRepository
from src.data.repositories.story import StoryRepository
from src.data.repositories.user import UserRepository
from src.data.schemas.auth import RegistrationData, UserResponse, UserRow
from src.data.schemas.story import CreateStoryRequest
from src.service.auth.service import AuthService
from src.service.exceptions import ConflictError
from src.service.story.service import StoryService


class BarrierUserRepository(UserRepository):
    def __init__(self, pool: asyncpg.Pool) -> None:
        super().__init__(pool)
        self._arrived = 0
        self._gate = asyncio.Event()
        self._lock = asyncio.Lock()

    async def get_by_email(self, email: str, executor=None):
        async with self._lock:
            self._arrived += 1
            if self._arrived == 2:
                self._gate.set()
        await self._gate.wait()
        return None


class BarrierStoryRepository(StoryRepository):
    def __init__(self, pool: asyncpg.Pool) -> None:
        super().__init__(pool)
        self._arrived = 0
        self._gate = asyncio.Event()
        self._lock = asyncio.Lock()

    async def exists_with_title(self, user_id: str, title: str) -> bool:
        async with self._lock:
            self._arrived += 1
            if self._arrived == 2:
                self._gate.set()
        await self._gate.wait()
        return False


def _assert_one_success_one_conflict(results: list[object]) -> None:
    assert sum(not isinstance(result, Exception) for result in results) == 1
    conflicts = [result for result in results if isinstance(result, ConflictError)]
    assert len(conflicts) == 1, (
        "database uniqueness is the final authority under concurrency; the losing "
        "request must surface as ConflictError, never a raw asyncpg exception or 500"
    )


async def test_concurrent_registration_maps_unique_race_to_conflict(
    clean_db: asyncpg.Pool,
) -> None:
    repo = BarrierUserRepository(clean_db)
    service = AuthService(
        repo,
        None,  # type: ignore[arg-type]
        AuthTokenRepository(clean_db),
        None,  # type: ignore[arg-type]
    )

    async def skip_email(user_id: str) -> None:
        return None

    service.send_verification_email = skip_email  # type: ignore[method-assign]

    payload = RegistrationData(
        username="same-user",
        email="race@example.com",
        password="Strong1!x",
    )

    results = await asyncio.gather(
        service.register_user(payload),
        service.register_user(payload),
        return_exceptions=True,
    )

    _assert_one_success_one_conflict(list(results))
    count = await clean_db.fetchval(
        'SELECT COUNT(*) FROM "user" WHERE email=$1',
        str(payload.email),
    )
    assert count == 1


async def test_concurrent_story_creation_maps_unique_race_to_conflict(
    clean_db: asyncpg.Pool,
    repo_user: UserRow,
) -> None:
    repo = BarrierStoryRepository(clean_db)
    service = StoryService(
        story_repo=repo,
        chapter_repo=None,  # type: ignore[arg-type]
        scene_repo=None,  # type: ignore[arg-type]
        provider=None,  # type: ignore[arg-type]
        search_config=None,  # type: ignore[arg-type]
        redis=None,  # type: ignore[arg-type]
    )
    payload = CreateStoryRequest(title="Race Story")

    results = await asyncio.gather(
        service.create_story(repo_user.id, payload),
        service.create_story(repo_user.id, payload),
        return_exceptions=True,
    )

    _assert_one_success_one_conflict(list(results))
    count = await clean_db.fetchval(
        'SELECT COUNT(*) FROM story WHERE user_id=$1 AND title=$2',
        repo_user.id,
        payload.title,
    )
    assert count == 1
