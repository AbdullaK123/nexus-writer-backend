import json
from src.data.models import Story
from src.data.schemas.extraction import PlotThread
from src.data.schemas.plot import PlotQuery, PlotThreadListResponse
from src.infrastructure.ai.enums import JobType
from src.service.exceptions import NotFoundError
from tortoise import Tortoise
from src.shared.schemas import ItemListResponse, ItemWithCount


async def get_plot_threads(story_id: str, query: PlotQuery) -> PlotThreadListResponse:

    story_exists = await Story.filter(id=story_id).exists()

    if not story_exists:
        raise NotFoundError("Story not found")
    
    conn = Tortoise.get_connection("default")

    results = await conn.execute_query_dict(
        """
        WITH latest AS (
            SELECT data
            FROM extraction 
            WHERE story_id=$1 AND type=$2
            ORDER BY created_at DESC
            LIMIT 1
        )
        SELECT
            e.is_stale,
            c->>'description' AS description,
            c->>'status' AS status,
            c->>'importance' AS importance,
            c->'tags' AS tags
        FROM latest e
        CROSS JOIN LATERAL jsonb_array_elements(e.data -> 'threads') c
        WHERE ($3::jsonb IS NULL OR c->'tags' @> $3::jsonb)
        AND ($4::text IS NULL OR c->>'status' = $4::text)
        AND ($5::text IS NULL OR c->>'importance' = $5::text)
        AND ($6::text IS NULL OR to_tsvector(
                'english',
                COALESCE(c->>'description', '')
            ) @@ websearch_to_tsquery('english', $6::text)
        )
        """,
        [
            story_id,
            JobType.PLOT_THREAD.value,
            json.dumps(query.tags) if query.tags else None,
            query.status.value if query.status else None,
            query.importance.value if query.importance else None,
            query.search_term
        ]
    )

    threads = [PlotThread(**{k:v for k, v in r.items() if k != "is_stale"}) for r in results]
    
    return PlotThreadListResponse(
        threads=threads,
        is_stale=results[0]["is_stale"] if results else False,
        num_found=len(threads)
    )


async def get_plot_tags(story_id: str) -> ItemListResponse:

    story_exists = await Story.filter(id=story_id).exists()

    if not story_exists:
        raise NotFoundError("Story not found")
    
    conn = Tortoise.get_connection("default")

    results = await conn.execute_query_dict(
        """
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
        CROSS JOIN LATERAL jsonb_array_elements(e.data -> 'threads') AS c
        CROSS JOIN LATERAL jsonb_array_elements_text(c->'tags') v
        GROUP BY v
        ORDER BY count DESC, v
        """,
        [story_id, JobType.PLOT_THREAD.value]
    )

    return ItemListResponse(
        items=[ItemWithCount(**r) for r in results]
    )