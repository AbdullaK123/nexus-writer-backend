from dependency_injector import containers, providers
from redis import Redis, ConnectionPool

from src.infrastructure.config import settings, config
from src.infrastructure.db.mongodb import MongoDB
from src.service.ai.utils.model_factory import create_chat_model

from src.data.repositories.mongo.character_extraction import CharacterExtractionRepo
from src.data.repositories.mongo.plot_extraction import PlotExtractionRepo
from src.data.repositories.mongo.structure_extraction import StructureExtractionRepo
from src.data.repositories.mongo.world_extraction import WorldExtractionRepo
from src.data.repositories.analytics.analytics import AnalyticsRepo

from src.service.auth.service import AuthService
from src.service.target.service import TargetService
from src.service.chapter.service import ChapterService
from src.service.story.service import StoryService
from src.service.jobs.service import JobService
from src.service.analytics.service import AnalyticsService
from src.service.analysis.character import CharacterService
from src.service.analysis.plot import PlotService
from src.service.analysis.structure import StructureService
from src.service.analysis.world import WorldConsistencyService
from src.service.analysis.character_tracker import CharacterTrackerService
from src.service.analysis.plot_tracker import PlotTrackerService


# ── Resource lifecycle functions ─────────────────────────────────────────

async def _init_mongodb():
    await MongoDB.connect(settings.mongodb_url)
    yield MongoDB.db
    await MongoDB.close()


def _init_redis_pool():
    pool = ConnectionPool.from_url(settings.redis_url)
    yield pool
    pool.disconnect()


# ── Container ────────────────────────────────────────────────────────────

class ApplicationContainer(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.app.controllers.auth",
            "src.app.controllers.chapter",
            "src.app.controllers.story",
            "src.app.controllers.jobs",
            "src.app.controllers.story_characters",
            "src.app.controllers.story_plot",
            "src.app.controllers.story_structure",
            "src.app.controllers.story_targets",
            "src.app.controllers.story_world",
            "src.app.channels.analytics",
            "src.service.auth.service",
        ],
    )

    # ── Infrastructure resources ─────────────────────────────────────

    mongodb = providers.Resource(_init_mongodb)

    redis_pool = providers.Resource(_init_redis_pool)

    redis_client = providers.Factory(Redis, connection_pool=redis_pool)

    # ── Shared AI model (singleton — one HTTP client for the process) ─

    chat_model = providers.Singleton(create_chat_model, config.ai.lite_model)

    # ── Repositories ─────────────────────────────────────────────────

    character_extraction_repo = providers.Singleton(CharacterExtractionRepo, db=mongodb)

    plot_extraction_repo = providers.Singleton(PlotExtractionRepo, db=mongodb)

    structure_extraction_repo = providers.Singleton(StructureExtractionRepo, db=mongodb)

    world_extraction_repo = providers.Singleton(WorldExtractionRepo, db=mongodb)

    analytics_repo = providers.Singleton(AnalyticsRepo, motherduck_url=settings.motherduck_url)

    # ── Core services (circular triangle wired post-init) ────────────

    auth_service = providers.Singleton(AuthService)

    target_service = providers.Singleton(TargetService)

    chapter_service = providers.Singleton(ChapterService, mongodb=mongodb)

    story_service = providers.Singleton(
        StoryService, mongodb=mongodb, target_service=target_service,
    )

    job_service = providers.Singleton(JobService, mongodb=mongodb)

    analytics_service = providers.Singleton(
        AnalyticsService,
        repo=analytics_repo,
        story_service=story_service,
        target_service=target_service,
    )

    # ── Analysis services ────────────────────────────────────────────

    character_service = providers.Singleton(
        CharacterService, repo=character_extraction_repo, model=chat_model,
    )

    plot_service = providers.Singleton(
        PlotService, repo=plot_extraction_repo, model=chat_model,
    )

    structure_service = providers.Singleton(
        StructureService, repo=structure_extraction_repo, model=chat_model,
    )

    world_service = providers.Singleton(
        WorldConsistencyService, repo=world_extraction_repo, model=chat_model,
    )

    character_tracker_service = providers.Singleton(
        CharacterTrackerService, repo=character_extraction_repo, model=chat_model,
    )

    plot_tracker_service = providers.Singleton(
        PlotTrackerService, repo=plot_extraction_repo, model=chat_model,
    )


def wire_circular_deps(container: ApplicationContainer):
    """Wire ChapterService ↔ JobService ↔ StoryService after construction."""
    chapter_svc = container.chapter_service()
    story_svc = container.story_service()
    job_svc = container.job_service()

    chapter_svc.job_service = job_svc
    story_svc.job_service = job_svc
    job_svc.chapter_service = chapter_svc
    job_svc.story_service = story_svc
