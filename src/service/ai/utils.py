from typing import List
from tortoise import Tortoise
from src.data.models.chapter import Chapter
from src.service.exceptions import NotFoundError


async def fetch_chapter_content(chapter_id: str) -> Chapter:
    chapter = await Chapter.filter(id=chapter_id).only("content", "id", "story").first()

    if chapter is None:
        raise NotFoundError("Chapter not found")
    return chapter


async def get_subsequent_chapter_ids(
    story_id: str, 
    starting_chapter_id: str
) -> List[str]:
    conn = Tortoise.get_connection("default")
    rows = await conn.execute_query_dict(
        """
        SELECT path_array[array_position(path_array, $1) : array_length(path_array, 1)] AS chapter_ids
        FROM story
        WHERE id = $2
        """,
        [starting_chapter_id, story_id],
    )
    if not rows:
        return []
    return rows[0]["chapter_ids"] or []