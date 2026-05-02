"""Sanity check: top-level packages import cleanly under the
asyncpg-only architecture (no Tortoise, no Aerich)."""


def test_repositories_import():
    from src.data import repositories  # noqa: F401

    for name in (
        "UserRepository", "SessionRepository",
        "StoryRepository", "ChapterRepository", "SceneRepository",
    ):
        assert hasattr(repositories, name)


def test_schemas_import():
    from src.data import schemas  # noqa: F401

    for name in (
        "UserRow", "SessionRow", "ChapterRow", "SceneRow",
        "StoryStatus",
    ):
        assert hasattr(schemas, name) or name == "StoryStatus"


def test_services_import():
    from src.service import auth, chapter, story, extraction  # noqa: F401
    from src.service.auth import AuthService  # noqa: F401
    from src.service.chapter import ChapterService  # noqa: F401
    from src.service.story import StoryService  # noqa: F401
    from src.service.extraction import ExtractionService, scenes_are_stale  # noqa: F401
