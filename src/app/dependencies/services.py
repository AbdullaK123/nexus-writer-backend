from fastapi import Depends
from redis.asyncio import Redis, ConnectionPool
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from tortoise import Tortoise
from pymongo.asynchronous.database import AsyncDatabase

from src.infrastructure.config import settings, config
from src.infrastructure.db.mongodb import MongoDB
from src.infrastructure.db.postgres import TORTOISE_ORM
from src.infrastructure.redis.job_registry import JobRegistry
from src.service.ai.utils.model_factory import create_chat_model
from src.shared.utils.decorators import singleton

from src.data.repositories.mongo.character_extraction import CharacterExtractionRepo
from src.data.repositories.mongo.plot_extraction import PlotExtractionRepo
from src.data.repositories.mongo.structure_extraction import StructureExtractionRepo
from src.data.repositories.mongo.world_extraction import WorldExtractionRepo
from src.data.repositories.analytics.analytics import AnalyticsRepo

from src.service.auth.service import AuthService
from src.service.target.service import TargetService
from src.service.chapter.service import ChapterService
from src.service.story.service import StoryService
from src.service.jobs import JobEventService, JobService
from src.service.analytics.service import AnalyticsService
from src.service.analytics.session_cache import SessionCacheService
from src.service.analysis.character import CharacterService
from src.service.analysis.plot import PlotService
from src.service.analysis.structure import StructureService
from src.service.analysis.world import WorldConsistencyService
from src.service.analysis.character_tracker import CharacterTrackerService
from src.service.analysis.plot_tracker import PlotTrackerService


# ── Infrastructure lifecycle ─────────────────────────────────────────

_redis_pool: ConnectionPool | None = None
_arq_pool: ArqRedis | None = None


async def init_infrastructure() -> None:
    global _redis_pool, _arq_pool
    await Tortoise.init(config=TORTOISE_ORM)
    await MongoDB.connect(settings.mongodb_url, config.mongo.database_name)
    _redis_pool = ConnectionPool.from_url(
        settings.redis_url,
        socket_connect_timeout=config.redis.socket_connect_timeout,
        socket_timeout=config.redis.socket_timeout,
    )
    _arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_broker_url))


async def shutdown_infrastructure() -> None:
    global _redis_pool, _arq_pool
    if _arq_pool:
        await _arq_pool.aclose()
        _arq_pool = None
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
    await MongoDB.close()
    await Tortoise.close_connections()


# ── Infrastructure dependencies ──────────────────────────────────────

def get_mongodb() -> AsyncDatabase:
    return MongoDB.db  # type: ignore[return-value]


def get_redis_pool() -> ConnectionPool:
    return _redis_pool  # type: ignore[return-value]


def get_redis_client(pool: ConnectionPool = Depends(get_redis_pool)) -> Redis:
    return Redis(connection_pool=pool)


def get_arq_pool() -> ArqRedis:
    if _arq_pool is None:
        raise RuntimeError("arq pool not initialized")
    return _arq_pool


def get_job_registry(pool: ArqRedis = Depends(get_arq_pool)) -> JobRegistry:
    return singleton(JobRegistry)(redis=pool)


def get_chat_model():
    return singleton(create_chat_model)(config.ai.lite_model)


# ── Repository dependencies ─────────────────────────────────────────

def get_character_extraction_repo(db: AsyncDatabase = Depends(get_mongodb)) -> CharacterExtractionRepo:
    return singleton(CharacterExtractionRepo)(db=db)


def get_plot_extraction_repo(db: AsyncDatabase = Depends(get_mongodb)) -> PlotExtractionRepo:
    return singleton(PlotExtractionRepo)(db=db)


def get_structure_extraction_repo(db: AsyncDatabase = Depends(get_mongodb)) -> StructureExtractionRepo:
    return singleton(StructureExtractionRepo)(db=db)


def get_world_extraction_repo(db: AsyncDatabase = Depends(get_mongodb)) -> WorldExtractionRepo:
    return singleton(WorldExtractionRepo)(db=db)


def get_analytics_repo() -> AnalyticsRepo:
    return singleton(AnalyticsRepo)(motherduck_url=settings.motherduck_url)


# ── Service dependencies ────────────────────────────────────────────

def get_auth_service() -> AuthService:
    return singleton(AuthService)()


def get_target_service() -> TargetService:
    return singleton(TargetService)()


def get_job_service(
    db: AsyncDatabase = Depends(get_mongodb),
    arq_pool: ArqRedis = Depends(get_arq_pool),
    registry: JobRegistry = Depends(get_job_registry),
) -> JobService:
    return singleton(JobService)(mongodb=db, arq_pool=arq_pool, registry=registry)


def get_job_event_service() -> JobEventService:
    return singleton(JobEventService)(redis_url=settings.redis_url)


def get_chapter_service(
    db: AsyncDatabase = Depends(get_mongodb),
    job_service: JobService = Depends(get_job_service),
) -> ChapterService:
    return singleton(ChapterService)(mongodb=db, job_service=job_service)


def get_story_service(
    db: AsyncDatabase = Depends(get_mongodb),
    target_service: TargetService = Depends(get_target_service),
    job_service: JobService = Depends(get_job_service),
) -> StoryService:
    return singleton(StoryService)(mongodb=db, target_service=target_service, job_service=job_service)


def get_analytics_service(
    repo: AnalyticsRepo = Depends(get_analytics_repo),
    story_service: StoryService = Depends(get_story_service),
    target_service: TargetService = Depends(get_target_service),
) -> AnalyticsService:
    return singleton(AnalyticsService)(repo=repo, story_service=story_service, target_service=target_service)


def get_session_cache_service(
    redis_client: Redis = Depends(get_redis_client),
) -> SessionCacheService:
    return singleton(SessionCacheService)(redis_client=redis_client)


def _socket_io_get_session_cache_service() -> SessionCacheService:
    return singleton(SessionCacheService)(redis_client=get_redis_client(pool=get_redis_pool()))


def _socket_io_get_analytics_service() -> AnalyticsService:
    return singleton(AnalyticsService)(
        repo=get_analytics_repo(),
        story_service=get_story_service(
            db=get_mongodb(),
            target_service=get_target_service(),
            job_service=get_job_service(
                db=get_mongodb(), 
                arq_pool=get_arq_pool(), 
                registry=singleton(JobRegistry)(
                    redis=get_arq_pool()
                )
            ),
        ),
        target_service=get_target_service(),
    )


def get_character_service(
    repo: CharacterExtractionRepo = Depends(get_character_extraction_repo),
    model=Depends(get_chat_model),
) -> CharacterService:
    return singleton(CharacterService)(repo=repo, model=model)


def get_plot_service(
    repo: PlotExtractionRepo = Depends(get_plot_extraction_repo),
    model=Depends(get_chat_model),
) -> PlotService:
    return singleton(PlotService)(repo=repo, model=model)


def get_structure_service(
    repo: StructureExtractionRepo = Depends(get_structure_extraction_repo),
    model=Depends(get_chat_model),
) -> StructureService:
    return singleton(StructureService)(repo=repo, model=model)


def get_world_service(
    repo: WorldExtractionRepo = Depends(get_world_extraction_repo),
    model=Depends(get_chat_model),
) -> WorldConsistencyService:
    return singleton(WorldConsistencyService)(repo=repo, model=model)


def get_character_tracker_service(
    repo: CharacterExtractionRepo = Depends(get_character_extraction_repo),
    model=Depends(get_chat_model),
) -> CharacterTrackerService:
    return singleton(CharacterTrackerService)(repo=repo, model=model)


def get_plot_tracker_service(
    repo: PlotExtractionRepo = Depends(get_plot_extraction_repo),
    model=Depends(get_chat_model),
) -> PlotTrackerService:
    return singleton(PlotTrackerService)(repo=repo, model=model)
