from dataclasses import dataclass
from functools import wraps
from typing import Awaitable, Callable, Literal

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from src.data.schemas.chapter import ChapterContentResponse, ChapterListItem
from src.data.schemas.scene import SceneSearchResponse
from src.service.chapter import ChapterService
from src.service.exceptions import ServiceError
from src.service.story import StoryService
from src.infrastructure.config import settings
from src.shared.utils.html import html_to_plain_text


def _service_errors_as_text(
    func: Callable[..., Awaitable[str]],
) -> Callable[..., Awaitable[str]]:
    """Catch ServiceError inside a tool and return its message as the tool
    result. Without this, the exception aborts the whole agent run instead
    of being fed back to the LLM as recoverable feedback."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> str:
        try:
            return await func(*args, **kwargs)
        except ServiceError as e:
            return f"Tool error: {e}"
    return wrapper


@dataclass
class ChatDeps:
    user_id: str
    story_id: str
    chapter_service: ChapterService
    story_service: StoryService


def _format_scene(
    response: SceneSearchResponse,
    chapter_title_by_id: dict[str, str],
) -> str:
    chapter_title = chapter_title_by_id.get(response.chapter_id, "(unknown)")
    lines = [
        f"TITLE: {response.title} (scene_id={response.id})",
        f"FROM CHAPTER: {chapter_title} (chapter_id={response.chapter_id})",
        f"TENSION: {response.tension}   PACING: {response.pacing}",
    ]
    if response.mentioned_entities:
        lines.append(f"ENTITIES: {', '.join(response.mentioned_entities)}")
    if response.tags:
        lines.append(f"TAGS: {', '.join(response.tags)}")
    lines.append(f"\nDESCRIPTION:\n{response.description}")
    if response.questions_raised:
        bullets = "\n".join(f"  - {q}" for q in response.questions_raised)
        lines.append(f"\nOPEN QUESTIONS RAISED:\n{bullets}")
    lines.append(
        f"\nSCENE STARTS AT (verbatim opening line): {response.start_quote!r}"
        f"\nSCENE ENDS AT (verbatim closing line):   {response.end_quote!r}"
    )
    return "\n".join(lines)


def _format_chapter(response: ChapterContentResponse, content: str) -> str:
    return (
        f"TITLE: {response.title} (chapter_id={response.id})\n\n"
        f"CONTENT:\n{content}"
    )


def _format_chapter_item(item: ChapterListItem) -> str:
    return f"TITLE: {item.chapter_title} (chapter_id={item.chapter_id})"


def build_agent(model_name: str) -> Agent[ChatDeps, str]:

    model = OpenRouterModel(
        model_name,
        provider=OpenRouterProvider(api_key=settings.open_router_api_key)
    )

    agent = Agent(
        model=model,
        deps_type=ChatDeps,
        system_prompt=(
            "You are a writing assistant helping the author explore their "
            "own story. Use the tools to look up scenes and chapters before "
            "answering. Never invent facts about the story.\n\n"
            "Tool guidance:\n"
            "- For broad recall (character threads, themes, dangling "
            "plotlines), run `search_scenes_semantic` with several distinct "
            "phrasings — one query rarely covers a topic exhaustively.\n"
            "- Search results include the parent `chapter_id` and chapter "
            "title for every scene; use those when citing chapters.\n"
            "- `get_chapter` takes a chapter_id ONLY. Scene ids are different "
            "and will fail. If unsure, call `list_chapters` first.\n"
            "- The `SCENE STARTS AT` / `SCENE ENDS AT` lines in search "
            "results are boundary anchors, not evidence — never cite them "
            "as quotations on their own.\n"
            "- To quote the prose of a scene you've already located via "
            "search, use `get_scene_text` (cheap, returns just that scene). "
            "To analyze chapter-level prose — style, voice, pacing, what "
            "exactly is said inside chapter X, or whether a chapter could "
            "be cut — use `get_chapter`. When the question names a specific "
            "chapter, read that chapter."
        ),
    )

    @agent.tool
    @_service_errors_as_text
    async def search_scenes_semantic(
        ctx: RunContext[ChatDeps],
        query: str,
        tension: Literal["low", "medium", "high"] | None = None,
        pacing: Literal["slow", "steady", "fast"] | None = None,
        tags: list[str] | None = None,
        pov: str | None = None,
        mentioned_entities: list[str] | None = None,
        chapter_ids: list[str] | None = None,
        k: int = 8,
    ) -> str:
        """Find scenes in the current story that are semantically related to
        the query. Returns up to k matches.

        Optional filters (combine freely; both default to no filter):
        - `tension`: restrict to scenes of a given dramatic tension level.
            'low' = calm/expository, 'medium' = active conflict / rising
            stakes, 'high' = climactic / irreversible / peak emotional beats.
            Use when the user asks about "big moments", "quiet scenes",
            "turning points", etc.
        - `pacing`: restrict to scenes of a given narrative pacing.
            'slow' = lingering / introspective, 'steady' = balanced forward
            motion, 'fast' = rapid action or revelations. Use when the user
            asks about "action scenes", "slow burns", "fast-paced sections",
            etc.
        - `tags`: restrict to scenes carrying ANY of the given tag labels
            (OR semantics, not AND). Tags are an OPEN VOCABULARY produced
            per-story by the extraction step (kebab-case, e.g.
            'turning-point', 'foreshadowing', 'betrayal', 'flashback',
            'worldbuilding', 'character-development'). Only pass values
            you've actually seen in prior search results for THIS story —
            guessing tag strings will silently return zero hits. Prefer
            running an unfiltered search first to learn the vocabulary,
            then re-query with a tag filter.
        - `mentioned_entities`: restrict to scenes that explicitly name ANY
            of the given entities (characters, locations, factions,
            artifacts). Also OPEN VOCABULARY — use the exact canonical
            spellings as they appear in scene results (e.g. 'Captain Vale',
            not 'vale' or 'the captain'). Same caveat as tags: only pass
            entity names you've seen in this story. Useful for "all scenes
            with X" or "scenes where X and Y appear" (pass both — OR
            semantics will return scenes mentioning either, then you can
            inspect which contain both).
        - `chapter_ids`: restrict to scenes inside specific chapters. Pass
            chapter ids gathered from `list_chapters` (which returns them
            in reading order). Useful for scoping analysis to an act or a
            range of chapters — e.g. "pacing in chapters 8-12" → grab those
            five ids from `list_chapters`, pass them all here. Ignored if
            empty / not given.

        For tag and entity filters, prefer calling `list_story_tags` /
        `list_story_entities` first to discover the exact vocabulary for
        this story rather than guessing. Guessed values silently return
        zero hits.

        Each match includes:

        - scene title + scene_id, parent chapter title + chapter_id
        - TENSION (low|medium|high) and PACING (slow|steady|fast)
        - ENTITIES: characters / places / artifacts present in the scene
        - TAGS: scene-function and mood labels (e.g. turning-point,
            foreshadowing, betrayal, worldbuilding)
        - DESCRIPTION: short prose summary
        - OPEN QUESTIONS RAISED: dangling threads the scene introduces — use
            these to track unresolved plot threads across the story
        - SCENE STARTS AT / SCENE ENDS AT: verbatim opening and closing
            lines of the scene. These are anchors marking scene boundaries,
            NOT evidence quotes. To get the prose between them, call
            `get_scene_text`. To read a whole chapter, call `get_chapter`.

        Pass `chapter_id` (NOT `scene_id`) to `get_chapter`."""
        scenes = await ctx.deps.story_service.search_story_scenes(
            user_id=ctx.deps.user_id,
            story_id=ctx.deps.story_id,
            query_text=query,
            k=k,
            tension=tension,
            pacing=pacing,
            pov=pov,
            tags=tags,
            mentioned_entities=mentioned_entities,
            chapter_ids=chapter_ids,
        )
        if not scenes:
            return "No matching scenes."
        chapters = await ctx.deps.chapter_service.get_story_chapters(
            story_id=ctx.deps.story_id,
            user_id=ctx.deps.user_id,
        )
        title_by_id = {c.chapter_id: c.chapter_title for c in chapters.chapters}
        return "\n\n".join(_format_scene(scene, title_by_id) for scene in scenes)

    @agent.tool
    @_service_errors_as_text
    async def get_chapter(
        ctx: RunContext[ChatDeps],
        chapter_id: str,
    ) -> str:
        """Read the full plain-text content of one chapter by its id.

        IMPORTANT: `chapter_id` must be a CHAPTER id, not a scene id. Get
        chapter ids from `list_chapters` or from the `chapter_id` field
        attached to each `search_scenes_semantic` result. Passing a scene_id
        here will return a 'not found' error."""
        chapter = await ctx.deps.chapter_service.get_chapter_with_navigation(
            chapter_id=chapter_id,
            user_id=ctx.deps.user_id,
            as_html=True,
        )
        return _format_chapter(chapter, content=html_to_plain_text(chapter.content))

    @agent.tool
    @_service_errors_as_text
    async def get_scene_text(
        ctx: RunContext[ChatDeps],
        chapter_id: str,
        start_quote: str,
        end_quote: str,
    ) -> str:
        """Return the verbatim prose of one scene from the chapter.

        Use this to quote actual scene content without paying for a full
        `get_chapter` read. `start_quote` and `end_quote` must be the
        exact `SCENE STARTS AT` / `SCENE ENDS AT` strings from a
        `search_scenes_semantic` result for the same `chapter_id`. Returns
        the chapter text from the start of `start_quote` through the end
        of `end_quote`, inclusive."""
        chapter = await ctx.deps.chapter_service.get_chapter_with_navigation(
            chapter_id=chapter_id,
            user_id=ctx.deps.user_id,
            as_html=True,
        )
        content = html_to_plain_text(chapter.content)
        start_idx = content.find(start_quote)
        if start_idx == -1:
            return (
                f"Tool error: start_quote not found in chapter {chapter_id!r}. "
                "Pass the exact `SCENE STARTS AT` value from a search result."
            )
        end_idx = content.find(end_quote, start_idx)
        if end_idx == -1:
            return (
                f"Tool error: end_quote not found after start_quote in chapter "
                f"{chapter_id!r}. Pass the exact `SCENE ENDS AT` value from "
                "the same search result."
            )
        return content[start_idx : end_idx + len(end_quote)]

    @agent.tool
    @_service_errors_as_text
    async def list_chapters(ctx: RunContext[ChatDeps]) -> str:
        """List every chapter in the current story in reading order. Returns
        title and chapter_id for each. Use this to get an outline of the
        story before drilling into specific chapters with `get_chapter`."""
        chapters = await ctx.deps.chapter_service.get_story_chapters(
            story_id=ctx.deps.story_id,
            user_id=ctx.deps.user_id,
        )
        if not chapters.chapters:
            return "This story has no chapters yet."
        return "\n".join(_format_chapter_item(item) for item in chapters.chapters)

    @agent.tool
    @_service_errors_as_text
    async def list_story_tags(ctx: RunContext[ChatDeps]) -> str:
        """List every distinct tag used in this story's scenes, with how
        many scenes carry each tag, sorted most-frequent first.

        Use this to discover the actual tag vocabulary BEFORE filtering
        `search_scenes_semantic` by `tags=[...]`. Tags are an open
        vocabulary produced per-story by extraction — guessing tag strings
        will silently return zero hits.

        Returns one line per tag: `tag_value (N scenes)`."""
        result = await ctx.deps.story_service.list_story_tags(
            user_id=ctx.deps.user_id, story_id=ctx.deps.story_id,
        )
        if not result.items:
            return "This story has no tagged scenes yet."
        return "\n".join(f"{i.value} ({i.count} scenes)" for i in result.items)

    @agent.tool
    @_service_errors_as_text
    async def list_story_entities(ctx: RunContext[ChatDeps]) -> str:
        """List every distinct named entity (character, place, faction,
        artifact) mentioned in this story's scenes, with how many scenes
        each appears in, sorted most-frequent first.

        Use this to discover the canonical entity spellings BEFORE
        filtering `search_scenes_semantic` by `mentioned_entities=[...]`.
        Entities are an open vocabulary produced per-story by extraction
        and are case- and form-sensitive (e.g. 'Captain Vale' vs 'Vale'
        are distinct). Guessed values silently return zero hits.

        Returns one line per entity: `entity_value (N scenes)`."""
        result = await ctx.deps.story_service.list_story_entities(
            user_id=ctx.deps.user_id, story_id=ctx.deps.story_id,
        )
        if not result.items:
            return "This story has no entities extracted yet."
        return "\n".join(f"{i.value} ({i.count} scenes)" for i in result.items)
    
    @agent.tool
    @_service_errors_as_text
    async def list_povs(ctx: RunContext[ChatDeps]) -> str:
        """List every distinct pov mentioned in this story's scenes, with how many scenes
        each appears in, sorted most-frequent first.

        Use this to discover a story's pov characters BEFORE 
        filtering 'search_scenes_semantic' by 'pov=...'. Povs
        are case- and form-sensitive (e.g. 'Captain Vale' vs 'Vale'
        are distinct). Guessed values will silently return no results.

        Returns one line per povs: `entity_value (N scenes)`."""
        result = await ctx.deps.story_service.list_povs(
            user_id=ctx.deps.user_id, story_id=ctx.deps.story_id,
        )
        if not result.items:
            return "This story has no pov characters extracted yet."
        return "\n".join(f"{i.value} ({i.count} scenes)" for i in result.items)

    return agent