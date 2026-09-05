import asyncio

import asyncpg

from src.data.repositories.auth_tokens import AuthTokenRepository
from src.data.repositories.session import SessionRepository
from src.data.repositories.user import UserRepository
from src.data.schemas.auth import AuthCredentials
from src.infrastructure.auth.password import hash_password
from src.service.auth.service import AuthService
from src.service.exceptions import AuthError


class BarrierConsumeRepository(AuthTokenRepository):
    def __init__(self, pool: asyncpg.Pool, participants: int) -> None:
        super().__init__(pool)
        self._participants = participants
        self._arrived = 0
        self._gate = asyncio.Event()
        self._lock = asyncio.Lock()

    async def consume(self, **kwargs):
        async with self._lock:
            self._arrived += 1
            if self._arrived == self._participants:
                self._gate.set()
        await self._gate.wait()
        return await super().consume(**kwargs)


def build_service(pool: asyncpg.Pool, token_repo: AuthTokenRepository) -> AuthService:
    return AuthService(
        UserRepository(pool),
        SessionRepository(pool),
        token_repo,
        None,  # type: ignore[arg-type]
    )


async def test_concurrent_verification_replay_has_exactly_one_winner(
    clean_db: asyncpg.Pool,
) -> None:
    user_repo = UserRepository(clean_db)
    user = await user_repo.create(
        username="verification-race",
        email="verification-race@example.com",
        password_hash=hash_password("Strong1!Password"),
        profile_img=None,
    )
    normal_repo = AuthTokenRepository(clean_db)
    token = await normal_repo.create(user_id=user.id, purpose="email_verification")

    # The shared test pool has max_size=5. Keep the barrier below pool capacity:
    # each participant already owns a connection when it reaches consume().
    participants = 4
    racing_repo = BarrierConsumeRepository(clean_db, participants=participants)
    service = build_service(clean_db, racing_repo)

    results = await asyncio.gather(
        *(service.verify_email(token) for _ in range(participants)),
        return_exceptions=True,
    )

    successes = [result for result in results if not isinstance(result, Exception)]
    failures = [result for result in results if isinstance(result, Exception)]

    assert len(successes) == 1, "a bearer verification token must have exactly one consumer"
    assert len(failures) == participants - 1
    assert all(isinstance(error, AuthError) for error in failures)
    assert await clean_db.fetchval(
        'SELECT email_verified FROM "user" WHERE id=$1', user.id
    ) is True
    assert await normal_repo.get(token=token, purpose="email_verification") is None


async def test_concurrent_password_resets_with_same_token_cannot_both_win(
    clean_db: asyncpg.Pool,
) -> None:
    user_repo = UserRepository(clean_db)
    user = await user_repo.create(
        username="reset-race",
        email="reset-race@example.com",
        password_hash=hash_password("Original1!Password"),
        profile_img=None,
        verified=True,
    )
    normal_repo = AuthTokenRepository(clean_db)
    token = await normal_repo.create(user_id=user.id, purpose="password_reset")
    racing_repo = BarrierConsumeRepository(clean_db, participants=2)
    service = build_service(clean_db, racing_repo)

    candidates = (
        ("A", "WinnerA1!Password"),
        ("B", "WinnerB2!Password"),
    )

    async def attempt(label: str, password: str):
        try:
            await service.reset_password(token, password)
            return label, password, None
        except Exception as exc:
            return label, password, exc

    results = await asyncio.gather(*(attempt(*candidate) for candidate in candidates))
    winners = [result for result in results if result[2] is None]
    losers = [result for result in results if result[2] is not None]

    assert len(winners) == 1, (
        "completion order must never allow two different credentials to consume the same reset token"
    )
    assert len(losers) == 1
    assert isinstance(losers[0][2], AuthError)

    _, winning_password, _ = winners[0]
    _, losing_password, _ = losers[0]

    authenticated = await service.authenticate_user(
        AuthCredentials(email=user.email, password=winning_password)
    )
    assert authenticated.id == user.id

    try:
        await service.authenticate_user(
            AuthCredentials(email=user.email, password=losing_password)
        )
    except AuthError:
        pass
    else:
        raise AssertionError("the losing concurrent reset password must never authenticate")

    assert await normal_repo.get(token=token, purpose="password_reset") is None
