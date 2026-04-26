"""Shared model-building helpers for service tests."""
from src.data.models import User, Story, Chapter


async def make_user(
    *, username: str = "tester", email: str = "t@example.com",
    password_hash: str = "hashed", profile_img: str | None = None,
) -> User:
    return await User.create(
        username=username, email=email,
        password_hash=password_hash, profile_img=profile_img,
    )


async def make_story(
    user: User, *, title: str = "Story", path_array: list[str] | None = None,
) -> Story:
    return await Story.create(
        user_id=user.id, title=title,
        path_array=path_array if path_array is not None else [],
    )


async def make_chapter(
    story: Story, user: User, *, title: str = "Ch", content: str = "<p>x</p>",
    word_count: int = 1, append_to_path: bool = True,
) -> Chapter:
    chapter = await Chapter.create(
        story_id=story.id, user_id=user.id,
        title=title, content=content, word_count=word_count,
    )
    if append_to_path:
        story.path_array = list(story.path_array or []) + [chapter.id]
        await story.save(update_fields=["path_array"])
    return chapter
