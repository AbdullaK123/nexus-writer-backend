from src.data.models.story import Story
from src.data.schemas.character import CharacterListResponse, CharacterQuery
from src.data.schemas.extraction import Character
from src.infrastructure.ai.enums import JobType
from src.service.exceptions import NotFoundError
import json
from tortoise import Tortoise



async def get_characters(story_id: str, query: CharacterQuery) -> CharacterListResponse:

    conn = Tortoise.get_connection("default")

    story_exists = await Story.filter(id=story_id).exists()

    if not story_exists:
        raise NotFoundError("Story not found")

    sql = """
    WITH latest AS (
        SELECT id, is_stale, data
        FROM extraction
        WHERE story_id = $1 AND type = $2
        ORDER BY created_at DESC
        LIMIT 1
    )
    SELECT
        e.is_stale                AS is_stale,
        c ->> 'name'              AS name,
        c -> 'aliases'            AS aliases,
        c ->> 'importance'        AS importance,
        c ->> 'status'            AS status,
        c ->> 'description'       AS description,
        c -> 'key_relationships'  AS key_relationships,
        c -> 'tags'               AS tags
    FROM latest e
    CROSS JOIN LATERAL jsonb_array_elements(e.data -> 'characters') AS c
    WHERE ($3::text  IS NULL OR c ->> 'importance' = $3)
    AND ($4::text  IS NULL OR c ->> 'status'     = $4)
    AND ($5::jsonb IS NULL OR c -> 'tags' @> $5::jsonb);
    """

    results = await conn.execute_query_dict(sql, [
        story_id,
        JobType.CHARACTER.value,
        query.importance,
        query.status,
        json.dumps(query.tags) if query.tags else None
    ])

    characters = [
        Character(
            name=result["name"],
            aliases=result["aliases"],
            importance=result["importance"],
            status=result["status"],
            description=result["description"],
            key_relationships=result["key_relationships"],
            tags=result["tags"]
        )
        for result in results
    ]

    is_stale = results[0]["is_stale"] if results else False

    return CharacterListResponse(roster=characters, is_stale=is_stale)
