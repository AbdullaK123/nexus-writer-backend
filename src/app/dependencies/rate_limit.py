import redis.asyncio as aioredis
from fastapi import Depends, Request
from loguru import logger
from redis.exceptions import RedisError

from src.app.dependencies.auth import get_current_user, get_verified_user
from src.app.dependencies.redis import get_redis
from src.data.schemas import UserRow
from src.infrastructure.redis.rate_limiting import consume_fixed_window
from src.service.exceptions import RateLimitError


async def _enforce_rate_limit(
    redis: aioredis.Redis,
    *,
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    try:
        allowed = await consume_fixed_window(
            redis,
            key=key,
            limit=limit,
            window_seconds=window_seconds,
        )
    except RedisError as exc:
        # Rate limiting is protective, not canonical application state.
        # If Redis is unavailable, preserve availability and log the failure.
        logger.warning("rate_limit.redis_unavailable", key=key, error=str(exc))
        return

    if not allowed:
        raise RateLimitError("Too many requests. Please try again later.")


def ip_rate_limit(*, prefix: str, limit: int, window_seconds: int = 60):
    async def dependency(
        request: Request,
        redis: aioredis.Redis = Depends(get_redis),
    ) -> None:
        ip = request.client.host if request.client is not None else "unknown"
        await _enforce_rate_limit(
            redis,
            key=f"rl:{prefix}:ip:{ip}",
            limit=limit,
            window_seconds=window_seconds,
        )

    return Depends(dependency)


def user_rate_limit(
    *,
    prefix: str,
    limit: int,
    window_seconds: int = 60,
    verified: bool = True,
):
    user_dependency = get_verified_user if verified else get_current_user

    async def dependency(
        user: UserRow = Depends(user_dependency),
        redis: aioredis.Redis = Depends(get_redis),
    ) -> None:
        await _enforce_rate_limit(
            redis,
            key=f"rl:{prefix}:user:{user.id}",
            limit=limit,
            window_seconds=window_seconds,
        )

    return Depends(dependency)


# Public auth operations get independent IP buckets so one action cannot
# accidentally consume another action's quota.
oauth_start_rate_limit = ip_rate_limit(prefix="auth:oauth-start", limit=20)
login_rate_limit = ip_rate_limit(prefix="auth:login", limit=10)
register_rate_limit = ip_rate_limit(prefix="auth:register", limit=5)
forgot_password_rate_limit = ip_rate_limit(prefix="auth:forgot-password", limit=5)
reset_password_rate_limit = ip_rate_limit(prefix="auth:reset-password", limit=10)

# Verification resend is tied to the authenticated account, not a shared NAT IP.
verification_email_rate_limit = user_rate_limit(
    prefix="auth:verification-email",
    limit=5,
    verified=False,
)

# High enough for the editor's 500 ms autosave cadence, while still bounding
# pathological write floods.
write_rate_limit = user_rate_limit(prefix="write", limit=180)

# Direct AI work is the expensive boundary and gets a much tighter budget.
ai_rate_limit = user_rate_limit(prefix="ai", limit=15)

# Semantic search is heavier than ordinary reads, but should still feel instant.
search_rate_limit = user_rate_limit(prefix="search", limit=120)
