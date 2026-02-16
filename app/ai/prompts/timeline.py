from typing import List, Dict
from toon import encode


STORY_TIMELINE_SYSTEM_PROMPT = """You are a narrative chronologist analyzing a complete story's temporal structure from accumulated context and plot extractions.

# WHAT TO EXTRACT

1. EVENTS: Every significant plot event in CHRONOLOGICAL ORDER (story-world time, not chapter order).
   - Include: turning points, battles, deaths, arrivals, departures, revelations, betrayals, major decisions.
   - Exclude: routine activities (eating, sleeping) unless they advance the plot.
   - Use the story's own time references for time_marker ("Day 3," "two weeks after the battle," "that evening").
   - Mark flashbacks/flash-forwards explicitly so chronological vs narrative order is clear.

2. DURATION & TIME SCALE: Total time the story covers and the primary unit of progression (hours, days, weeks, months, years).

3. NARRATIVE STRUCTURE: Whether the story is strictly linear or uses flashbacks, flash-forwards, or parallel timelines.

4. TIMELINE GAPS: Places where time passage is genuinely unclear — NOT intentional ellipses or time-skips, only moments where a reader would be confused about when something happens. Each gap must name the specific chapters and state what's ambiguous.

5. TEMPORAL INCONSISTENCIES: Contradictions or impossibilities in timing. Must cite specific evidence from specific chapters.
   - Example: "Ch. 5 says the journey takes 3 days, but Ch. 8 shows arrival the next morning."
   - Do NOT flag intentional narrative devices (unreliable narrator, in-universe confusion) as inconsistencies.

6. CLARITY ASSESSMENT: How easy is it for a reader to follow this story's timeline? Factor in whether confusion is intentional (mystery) vs accidental (sloppy writing).

7. RECOMMENDATIONS: 3-5 specific, actionable fixes referencing chapter numbers.
   - Good: "Add a time marker at the start of Ch. 9 to clarify how much time passed since Ch. 8."
   - Bad: "Improve clarity." / "Add more time references."

# RULES
- Use the story's own terminology for time references — don't impose a system the author doesn't use.
- Chronological order = when events ACTUALLY happened in the story world, not when the reader encounters them.
- Only flag gaps that would genuinely confuse a careful reader, not every time skip.
- Inconsistencies must cite SPECIFIC textual evidence from SPECIFIC chapters.
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