import json
from typing import cast
from src.data.schemas.extraction import CulturalFact, Entity, Faction, HistoricalEvent, OtherWorldFact, Place, TechnologyOrSystem
from src.data.models import Story
from src.data.schemas.world import EntityListResponse, EntityQuery, EntityType
from tortoise import Tortoise
from src.infrastructure.ai.enums import JobType
from src.service.exceptions import NotFoundError
from src.service.utils.decorators import handle_service_errors, retry_on_operational_error
from src.shared.schemas import ItemListResponse, ItemWithCount


ENTITY_MAP = {
    EntityType.PLACES: Place,
    EntityType.FACTIONS: Faction,
    EntityType.TECHNOLOGIES: TechnologyOrSystem,
    EntityType.HISTORICAL_EVENTS: HistoricalEvent,
    EntityType.OTHER: OtherWorldFact,
    EntityType.CULTURAL_FACTS: CulturalFact
}

@handle_service_errors
@retry_on_operational_error
async def get_entities_by_type(
    story_id: str, 
    entity_type: EntityType,
    query: EntityQuery
) -> EntityListResponse:
    
    if entity_type not in ENTITY_MAP:
        raise ValueError(f"unknown entity type: {entity_type}")

    story_exists = await Story.filter(id=story_id).exists()

    if not story_exists:
        raise NotFoundError("Story not found")
    
    conn = Tortoise.get_connection("default")
    
    sql = f"""
    WITH latest AS (
        SELECT 
            is_stale,
            data
        FROM extraction
        WHERE story_id=$1 AND type=$2
        ORDER BY created_at DESC
        LIMIT 1
    )
    SELECT
        e.is_stale,
        c ->> 'name' AS name,
        c ->> 'description' AS description,
        c ->> 'importance' AS importance,
        c -> 'tags' AS tags
    FROM latest e
    CROSS JOIN LATERAL jsonb_array_elements(e.data -> '{entity_type.value}') AS c
    WHERE ($3::text IS NULL OR c->> 'importance' = $3::text)
    AND ($4::jsonb IS NULL OR c->'tags' @> $4::jsonb)
    AND (
        $5::text IS NULL OR to_tsvector(
            'english',
            COALESCE(c->>'name', '') || ' ' || 
            COALESCE(c->>'description', '')        
        ) @@ websearch_to_tsquery('english', $5)
    )
    """

    results = await conn.execute_query_dict(
        sql,
        [
            story_id,
            JobType.WORLD_BIBLE.value,
            query.importance.value if query.importance else None,
            json.dumps(query.tags) if query.tags else None,
            query.search_term
        ]
    )

    entities = cast(
        list[Entity],
        [ENTITY_MAP[entity_type](**{k: v for k, v in r.items() if k != "is_stale"}) for r in results],
    )

    is_stale = results[0]["is_stale"] if results else False

    return EntityListResponse(
        entities=entities,
        num_found=len(entities),
        is_stale=is_stale
    )


@handle_service_errors
@retry_on_operational_error
async def get_tags_by_type(
    story_id: str,
    entity_type: EntityType
) -> ItemListResponse:
     
    if entity_type not in ENTITY_MAP:
        raise ValueError(f"unknown entity type: {entity_type}")

    story_exists = await Story.filter(id=story_id).exists()

    if not story_exists:
        raise NotFoundError("Story not found")
    
    conn = Tortoise.get_connection("default")

    results = await conn.execute_query_dict(
        f"""
        WITH latest AS (
            SELECT data
            FROM extraction
            WHERE story_id=$1 AND type=$2
            ORDER BY created_at DESC
            LIMIT 1
        )
        SELECT
            v AS value,
            COUNT(*) AS count
        FROM latest e
        CROSS JOIN LATERAL jsonb_array_elements(e.data -> '{entity_type.value}') AS c
        CROSS JOIN LATERAL jsonb_array_elements_text(c->'tags') AS v
        GROUP BY v
        ORDER BY count DESC, value
        """,
        [story_id, JobType.WORLD_BIBLE.value]
    )

    return ItemListResponse(
        items=[ItemWithCount(**r) for r in results]
    )
    