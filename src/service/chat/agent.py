from dataclasses import dataclass
from functools import wraps
from typing import Awaitable, Callable

from pydantic_ai import Agent, RunContext

from src.data.schemas.chapter import ChapterContentResponse, ChapterListItem
from src.data.schemas.scene import SceneSearchResponse
from src.service.chapter import ChapterService
from src.service.exceptions import ServiceError
from src.service.story import StoryService
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
    return f"TITLE: {item.title} (chapter_id={item.id})"


def build_agent(model_name: str) -> Agent[ChatDeps, str]:

    agent = Agent(
        model=model_name,
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
        k: int = 8,
    ) -> str:
        """Find scenes in the current story that are semantically related to
        the query. Returns up to k matches. Each match includes:

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
        )
        if not scenes:
            return "No matching scenes."
        chapters = await ctx.deps.chapter_service.get_story_chapters(
            story_id=ctx.deps.story_id,
            user_id=ctx.deps.user_id,
        )
        title_by_id = {c.id: c.title for c in chapters.chapters}
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

    return agent