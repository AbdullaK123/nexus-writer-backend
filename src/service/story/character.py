from typing import Literal
from src.data.models.story import Story
from src.data.schemas.character import  CharacterListResponse, CharacterQuery
from src.shared.schemas import ItemListResponse, ItemWithCount
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
        c -> 'tags'               AS tags,
        c ->> 'arc'               AS arc,
        c ->> 'arc_type'          AS arc_type
    FROM latest e
    CROSS JOIN LATERAL jsonb_array_elements(e.data -> 'characters') AS c
    WHERE ($3::text  IS NULL OR c ->> 'importance' = $3)
    AND ($4::text  IS NULL OR c ->> 'status'     = $4)
    AND ($5::jsonb IS NULL OR c -> 'tags' @> $5::jsonb)
    AND ($6::jsonb IS NULL OR c -> 'aliases' @> $6::jsonb)
    AND ($7::jsonb IS NULL OR c -> 'key_relationships' @> $7::jsonb)
    AND (
        $8::text IS NULL OR to_tsvector(
            'english',
            COALESCE(c ->> 'name', '') || ' ' ||
            COALESCE(c ->> 'description', '') || ' ' ||
            COALESCE(c ->> 'arc', '') || ' ' ||
            COALESCE((SELECT string_agg(value, ' ') FROM jsonb_array_elements_text(c -> 'aliases')), '')
        ) @@ websearch_to_tsquery('english', $8)
    )
    AND ($9::text IS NULL OR c ->> 'arc_type' = $9)
    """

    results = await conn.execute_query_dict(sql, [
        story_id,
        JobType.CHARACTER.value,
        query.importance,
        query.status,
        json.dumps(query.tags) if query.tags else None,
        json.dumps(query.aliases) if query.aliases else None,
        json.dumps(query.key_relationships) if query.key_relationships else None,
        query.search_term,
        query.arc_type
    ])

    characters = [Character(**{k: v for k, v in r.items() if k != "is_stale"}) for r in results]

    is_stale = results[0]["is_stale"] if results else False

    return CharacterListResponse(roster=characters, is_stale=is_stale, num_found=len(characters))


async def _get_character_facet(story_id: str, field: Literal["tags", "aliases", "key_relationships"]) -> list[dict]:
    if not await Story.filter(id=story_id).exists():
        raise NotFoundError("Story not found")

    conn = Tortoise.get_connection("default")
    return await conn.execute_query_dict(
        f"""
        WITH latest AS (
            SELECT data FROM extraction
            WHERE story_id = $1 AND type = $2
            ORDER BY created_at DESC LIMIT 1
        )
        SELECT v AS value, COUNT(*) AS count
        FROM latest AS e
        CROSS JOIN LATERAL jsonb_array_elements(e.data -> 'characters') AS c
        CROSS JOIN LATERAL jsonb_array_elements_text(c -> '{field}') AS v
        GROUP BY v
        ORDER BY count DESC, value
        """,
        [story_id, JobType.CHARACTER.value],
    )


async def get_all_character_tags(story_id: str) -> ItemListResponse:

    results = await _get_character_facet(story_id, "tags")

    return ItemListResponse(
        items=[ItemWithCount(**r) for r in results]
    )


async def get_all_character_aliases(story_id: str) -> ItemListResponse:    

    results = await _get_character_facet(story_id, "aliases")

    return ItemListResponse(
        items=[ItemWithCount(**r) for r in results]
    )


async def get_all_character_key_relationships(story_id: str) -> ItemListResponse:    

    results = await _get_character_facet(story_id, "key_relationships")

    return ItemListResponse(
        items=[ItemWithCount(**r) for r in results]
    )