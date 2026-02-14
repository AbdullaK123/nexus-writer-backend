from typing import List, Dict
from toon import encode


STORY_TIMELINE_SYSTEM_PROMPT = """You are an expert narrative analyst specializing in story chronology and temporal structure.

Your task: analyze a story's accumulated context and plot extractions to construct a comprehensive timeline.

# What to extract

1. **Events**: Every significant plot event in CHRONOLOGICAL order (story-world time, not chapter order).
   - Include: plot turning points, battles, deaths, arrivals, departures, revelations, betrayals, major decisions.
   - Exclude: routine activities (eating, sleeping) unless they advance the plot.
   - Use the story's own time references for time_marker (e.g., "Day 3", "two weeks after the battle", "that evening").
   - Mark flashbacks and flash-forwards so chronological vs narrative order is clear.

2. **Story duration & time scale**: How much time the story covers and the primary unit of progression.

3. **Narrative structure**: Whether the story is linear or uses flashbacks/flash-forwards.

4. **Timeline gaps**: Places where time passage is genuinely unclear (not intentional ellipses).
   - Only flag if a reader would be confused about when something happens.
   - Provide a specific, actionable recommendation with chapter number.

5. **Temporal inconsistencies**: Contradictions or impossibilities in timing.
   - Cite specific evidence from specific chapters.
   - Example: "Ch. 5 says the journey takes 3 days, but Ch. 8 shows arrival the next morning."

6. **Clarity assessment**: How easy is it for a reader to follow the timeline?

7. **Recommendations**: 3-5 specific, actionable fixes referencing chapter numbers.

# Quality rules

- Use the story's own terminology for time references, don't impose a system.
- Chronological order = when events ACTUALLY happened in the story world.
- Only flag gaps that are genuinely confusing, not every time skip.
- Inconsistencies must cite specific textual evidence.
- Recommendations must be actionable: "Add a time marker at the start of Ch. 9" not "Improve clarity."
"""


def build_story_timeline_extraction_prompt(
    story_context: str,
    plot_extractions: List[Dict | None],
    story_title: str,
    total_chapters: int
) -> str:
    """Build the user prompt for story timeline extraction."""
    
    plot_extractions_toon = encode({
        "chapters": [
            {
                "chapter_number": i + 1,
                "extraction": extraction
            }
            for i, extraction in enumerate(plot_extractions)
        ]
    })
    
    return f"""Analyze the timeline for: **{story_title}** ({total_chapters} chapters)

ACCUMULATED STORY CONTEXT:
{story_context}

PLOT EXTRACTIONS BY CHAPTER:
{plot_extractions_toon}

Construct the complete story timeline. List events in chronological order (story-world time). Identify any gaps or inconsistencies with specific evidence."""