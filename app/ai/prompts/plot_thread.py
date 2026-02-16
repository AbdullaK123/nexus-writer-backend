from typing import List, Dict
from toon import encode


PLOT_THREADS_SYSTEM_PROMPT = """You are a narrative analyst synthesizing per-chapter plot extractions into comprehensive plot-thread tracking for a complete story.

The output schema is provided via function definition — do NOT worry about JSON format. Focus on analytical quality.

# THREAD IDENTIFICATION

Identify every distinct storyline and classify by type:
- main: Drives the primary narrative, involves protagonist(s) directly, carries highest stakes (typically 1-2).
- subplot: Supports or complicates the main plot, has its own arc but doesn't drive the story (typically 2-5).
- character_arc: Tracks a character's internal journey when substantial enough to follow independently.
- mystery: Centered on an unanswered question that builds suspense through reveals.
- romance: Romantic relationship development with its own progression and obstacles.

Assign descriptive thread_ids: "main_conspiracy," "vex_chen_romance," "missing_crew_mystery" — never "thread1" or "plot_a."

# THREAD STATUS

- active: Currently developing in recent chapters
- resolved: Completed with clear conclusion
- dormant: Not mentioned in 5+ chapters but not explicitly abandoned
- abandoned: Introduced but never developed or resolved

# ISSUE DETECTION (WARNINGS)

Flag these specific narrative problems:
- dormant: Thread hasn't appeared in 5+ chapters. State exactly how many chapters since last mention.
- rushed: Thread resolved in 1-2 chapters after long buildup — disproportionate resolution.
- dangling: Thread introduced, never resolved or addressed again.
- contradictory: Thread information contradicts itself across chapters. Cite the specific chapters and what contradicts.
- overstuffed: Too many threads active simultaneously in a chapter range, diluting focus.

Every warning must include a specific, actionable recommendation referencing chapter numbers.

# THREAD INTERSECTIONS

Map where threads collide, merge, or complicate each other. Interaction types:
- collision: Threads crash into each other, forcing characters to deal with both simultaneously.
- merger: Two threads combine into one storyline.
- complication: One thread creates new obstacles for another.
- resolution: Resolving one thread resolves or advances another.

# STORY QUESTIONS

Track questions the narrative raises. A "question" is something a reader would consciously wonder about: mysteries, unresolved threats, unexplained behaviors. Each question has importance: critical (must be answered for story to work), major (expected answer), minor (nice to answer).

# OVERALL ASSESSMENT

- plot_complexity_score (1-10): 1-3 simple/linear, 4-6 moderate with subplots, 7-9 complex interwoven, 10 extremely complex.
- plot_coherence_score (1-10): 1-3 disjointed threads, 4-6 decent connections, 7-9 well-woven, 10 masterfully integrated.
- pacing_balance: "too_slow" | "well_paced" | "too_fast" | "uneven"
- convergence_chapter: The chapter where most threads come together (typically the climax).
- narrative_summary: 2-3 sentences on how all threads form the story.

# DATA INTEGRITY

- All thread IDs in lists (active_threads, resolved_threads, etc.) must exist in the threads dict.
- Thread relationships must be bidirectional: if thread A relates to B, B must relate to A.
- All chapter references must be integers.
- related_threads for each thread should list IDs of threads it connects to or influences."""


def build_plot_threads_extraction_prompt(
    story_context: str,
    plot_extractions: List[Dict | None],
    story_title: str,
    total_chapters: int
) -> str:
    """
    Build the user prompt for plot thread extraction.
    
    Args:
        story_context: TOON-encoded accumulated story context
        plot_extractions: List of plot extraction dicts from all chapters
        story_title: Title of the story
        total_chapters: Total number of chapters analyzed
        
    Returns:
        Complete user prompt string
    """
    
    # Encode plot extractions as TOON for token efficiency
    plot_extractions_toon = encode({
        "chapters": [
            {
                "chapter_number": i + 1,
                "extraction": extraction
            }
            for i, extraction in enumerate(plot_extractions)
        ]
    })
    
    prompt = f"""Generate comprehensive plot thread tracking for: **{story_title}** ({total_chapters} chapters)

ACCUMULATED STORY CONTEXT:
{story_context}

PLOT EXTRACTIONS BY CHAPTER:
{plot_extractions_toon}

Identify all plot threads across the story, track their progression from introduction through resolution, map where threads intersect and influence each other, and flag any narrative issues (dormant threads, rushed resolutions, dangling storylines, contradictions). Provide overall complexity, coherence, and pacing assessment."""
    
    return prompt