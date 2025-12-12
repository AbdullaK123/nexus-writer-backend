from typing import List, Dict
from toon import encode


PLOT_THREADS_SYSTEM_PROMPT = """You are an expert narrative analyst specializing in plot structure, story threads, and dramatic tension.

Your task is to analyze a story's accumulated context and all plot extraction data to generate comprehensive plot thread tracking.

# Your Responsibilities

1. **Identify all plot threads** across the entire story (main plots, subplots, character arcs, mysteries)
2. **Track thread progression** from introduction through resolution (or lack thereof)
3. **Map thread intersections** where storylines collide, merge, or complicate each other
4. **Detect narrative issues** (dormant threads, rushed resolutions, dangling threads, contradictions)
5. **Assess story structure** (complexity, coherence, pacing balance)

# Quality Standards

- **Thread descriptions** should be 2-3 sentences capturing the core conflict/journey
- **Stakes** should be clear and specific to what's at risk
- **Obstacles** should track actual complications from the story
- **Story questions** should be precise, answerable questions the narrative raises
- **Warnings** should be actionable and specific

# Important Notes

- Focus on **what actually appears in the story**, not what should happen
- A thread is "dormant" if not mentioned for 5+ chapters
- A thread is "abandoned" if introduced but never developed or resolved
- Track foreshadowing and setup/payoff relationships
- Main threads drive the primary narrative; subplots support but don't drive
- Character arcs can be their own threads if substantial enough

# Output Format

Return a complete PlotThreadsExtraction with:
- All threads mapped by thread_id
- Status tracking for each thread
- Thread intersections and relationships
- Warnings for potential issues
- Overall narrative assessment

Be thorough, insightful, and true to the story."""


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
    
    prompt = f"""# STORY ANALYSIS TASK

Generate comprehensive plot thread tracking for: **{story_title}**

Total chapters analyzed: {total_chapters}

{'═' * 80}

# ACCUMULATED STORY CONTEXT (TOON Format)

{story_context}

{'═' * 80}

# PLOT EXTRACTIONS BY CHAPTER (TOON Format)

Below are the plot-focused extractions from each chapter, showing:
- Events and developments
- Plot threads mentioned
- Conflicts and obstacles
- Questions raised or answered
- Foreshadowing and setup

{plot_extractions_toon}

{'═' * 80}

# YOUR TASK: PLOT THREAD ANALYSIS

Analyze all the data above and create comprehensive plot thread tracking.

## Step 1: Identify All Plot Threads

Scan through all plot extractions to identify distinct storylines:

**Main Plot Threads:**
- Drive the primary narrative
- Involve the protagonist(s) directly
- Carry the highest stakes
- Typically 1-2 main threads

**Subplots:**
- Support or complicate the main plot
- May involve secondary characters
- Have their own arcs but don't drive the story
- Typically 2-5 subplots

**Character Arc Threads:**
- Focus on a character's internal journey
- Substantial enough to be tracked separately
- Example: "Vex's journey from isolation to connection"

**Mystery Threads:**
- Centered around an unanswered question
- Build suspense through reveals
- Example: "Who planted the artifact?"

**Romance Threads:**
- Romantic relationship development
- Has its own progression and obstacles
- Example: "Vex/Chen slow-burn romance"

For each thread, assign a unique **thread_id** (lowercase, underscores, descriptive):
- Good: "main_conspiracy", "vex_chen_romance", "missing_crew_mystery"
- Bad: "thread1", "plot_a", "thing"

## Step 2: Analyze Thread Status

For each thread, determine:

**Status:**
- "active" - Currently developing in recent chapters
- "resolved" - Completed with clear conclusion
- "dormant" - Not mentioned in 5+ chapters but not abandoned
- "abandoned" - Introduced but never developed or resolved

**Last Mentioned Chapter:**
Track the most recent chapter where this thread appeared.

**Chapters Since Mention:**
Calculate how many chapters since last mention (for dormancy tracking).

## Step 3: Map Thread Details

For each thread, extract:

**Basic Info:**
- `name`: Short, clear name (e.g., "The Alien Conspiracy")
- `thread_type`: "main", "subplot", "character_arc", "mystery", or "romance"
- `description`: 2-3 sentence summary of what this thread is about
- `introduced_chapter`: When thread first appeared
- `resolved_chapter`: When resolved (null if still active)
- `key_chapters`: Chapters with major developments

**Stakes and Goals:**
- `stakes`: What's at risk? What are the consequences of failure?
  Example: "Survival of entire fleet and exposure of military corruption"
- `goal`: What needs to be achieved to resolve this?
  Example: "Expose conspiracy, secure artifact, clear Vex's name"

**Characters:**
- `primary_characters`: Main drivers of this thread
- `supporting_characters`: Involved but not driving

**Complications:**

**obstacles** (list of PlotThreadObstacle):
```json
{{
  "obstacle": "Admiral blocking investigation",
  "introduced_chapter": 7,
  "resolved_chapter": 27,  // null if still blocking
  "resolution": "Admiral exposed and removed from command"  // null if unresolved
}}
```

**twists** (list of PlotThreadTwist):
```json
{{
  "chapter": 18,
  "twist": "Chen reveals she's been working with the conspiracy",
  "impact": "Forces Vex to choose between duty and personal loyalty"
}}
```

**Story Questions:**

Track questions raised by this thread:
```json
{{
  "question": "Who planted the artifact?",
  "raised_chapter": 5,
  "answered_chapter": 28,  // null if unanswered
  "answer": "Rogue faction of military scientists",  // null if unanswered
  "importance": "critical"  // "critical", "major", or "minor"
}}
```

**Foreshadowing:**
- List elements that hint at future developments
- Example: ["Chen's secretive behavior in Ch. 8", "Mention of 'Project Orpheus' in Ch. 12"]

**Setup/Payoff:**
- `setup_chapters`: Chapters that plant seeds for later payoffs
- `payoff_chapters`: Chapters where earlier setups pay off
- Track these relationships for narrative satisfaction

**Resolution (if resolved):**
- `resolution_summary`: How was it resolved? (2-3 sentences)
- `resolution_satisfaction`: "satisfying", "rushed", "anticlimactic", or "unresolved"

## Step 4: Map Thread Relationships

Identify where threads intersect:

**Thread Intersections:**
```json
{{
  "thread_1_id": "main_conspiracy",
  "thread_2_id": "vex_chen_romance",
  "intersection_chapter": 18,
  "interaction_type": "complication",  // "collision", "merger", "complication", "resolution"
  "description": "Chen's involvement in conspiracy threatens romance"
}}
```

**Related Threads:**
For each thread, list IDs of threads it connects to or influences.

## Step 5: Detect Issues and Generate Warnings

Scan for potential narrative problems:

**Dormant Threads** (not mentioned in 5+ chapters):
```json
{{
  "thread_id": "missing_crew_mystery",
  "warning_type": "dormant",
  "severity": "moderate",
  "description": "Thread hasn't been mentioned in 8 chapters (last: Ch. 12, current: Ch. 20)",
  "recommendation": "Either resolve in next 2-3 chapters or reintroduce with new development"
}}
```

**Rushed Resolutions** (resolved in 1-2 chapters after long buildup):
```json
{{
  "thread_id": "kora_betrayal",
  "warning_type": "rushed",
  "severity": "major",
  "description": "Thread built over 20 chapters, resolved in single chapter without proper development",
  "recommendation": "Consider expanding resolution across 2-3 chapters for emotional impact"
}}
```

**Dangling Threads** (introduced but never resolved):
```json
{{
  "thread_id": "artifact_origin",
  "warning_type": "dangling",
  "severity": "major",
  "description": "Mystery introduced in Ch. 5, never addressed or resolved",
  "recommendation": "Either resolve before story ends or acknowledge as intentional open question"
}}
```

**Contradictory Threads** (threads that contradict each other):
```json
{{
  "thread_id": "main_conspiracy",
  "warning_type": "contradictory",
  "severity": "major",
  "description": "Ch. 10 establishes Admiral as mastermind, Ch. 22 reveals it's someone else with no explanation",
  "recommendation": "Add dialogue or exposition explaining the misdirection"
}}
```

**Overstuffed** (too many active threads simultaneously):
```json
{{
  "thread_id": "multiple",
  "warning_type": "overstuffed",
  "severity": "moderate",
  "description": "Chapters 15-18 juggle 7 active threads simultaneously, diluting focus",
  "recommendation": "Consider resolving 2-3 minor threads to focus on main storylines"
}}
```

## Step 6: Calculate Statistics

**Thread Counts:**
- `total_threads`: Total number of threads identified
- `active_threads`: List of thread IDs currently active
- `resolved_threads`: List of thread IDs that are resolved
- `dormant_threads`: List of thread IDs not mentioned in 5+ chapters
- `abandoned_threads`: List of thread IDs introduced but never developed

**Thread Categories:**
- `main_threads`: IDs of main plot threads
- `subplots`: IDs of subplot threads
- `character_arcs`: IDs of character arc threads

**Story Questions:**
- `unanswered_questions`: All questions still open
- `answered_questions`: All questions that have been answered

## Step 7: Assess Overall Structure

**Complexity Score (1-10):**
Rate plot complexity:
- 1-3: Simple, linear plot
- 4-6: Moderate complexity with subplots
- 7-9: Complex, interwoven threads
- 10: Extremely complex, may be confusing

**Coherence Score (1-10):**
Rate how well threads weave together:
- 1-3: Disjointed, threads feel disconnected
- 4-6: Decent connections, some loose threads
- 7-9: Well-woven, threads enhance each other
- 10: Masterfully integrated

**Pacing Balance:**
- "too_slow": Threads advancing at glacial pace
- "well_paced": Good balance of development
- "too_fast": Threads rushing to resolution
- "uneven": Some threads too fast, others too slow

**Convergence Chapter:**
Identify the chapter where most threads come together (typically the climax).

**Threads Per Chapter:**
Map chapter numbers to active thread IDs for that chapter.

**Narrative Summary:**
2-3 sentence overview of how all threads work together to form the story.

{'═' * 80}

# OUTPUT SCHEMA

Return JSON matching this exact structure:
```json
{{
  "threads": {{
    "thread_id": {{
      "thread_id": "main_conspiracy",
      "name": "The Alien Conspiracy",
      "thread_type": "main",
      "description": "Discovery of alien artifact leads to...",
      "status": {{
        "status": "active",
        "last_mentioned_chapter": 25,
        "chapters_since_mention": 0
      }},
      "introduced_chapter": 3,
      "resolved_chapter": null,
      "key_chapters": [3, 7, 12, 18, 25],
      "stakes": "Survival of entire fleet...",
      "goal": "Expose conspiracy, secure artifact...",
      "primary_characters": ["Commander Vex", "Admiral Kora"],
      "supporting_characters": ["Dr. Chen", "Lieutenant Park"],
      "obstacles": [
        {{
          "obstacle": "Admiral blocking investigation",
          "introduced_chapter": 7,
          "resolved_chapter": 27,
          "resolution": "Admiral exposed and removed"
        }}
      ],
      "twists": [
        {{
          "chapter": 18,
          "twist": "Chen's involvement revealed",
          "impact": "Forces Vex to choose loyalty vs duty"
        }}
      ],
      "questions_raised": [
        {{
          "question": "Who planted the artifact?",
          "raised_chapter": 5,
          "answered_chapter": 28,
          "answer": "Rogue military faction",
          "importance": "critical"
        }}
      ],
      "foreshadowing": ["Chen's secretive behavior Ch. 8"],
      "setup_chapters": [5, 12],
      "payoff_chapters": [28, 30],
      "resolution_summary": "Conspiracy exposed, artifact secured...",
      "resolution_satisfaction": "satisfying",
      "related_threads": ["vex_chen_romance", "kora_betrayal"],
      "pacing_notes": "Well-paced development with good escalation"
    }}
  }},
  "total_threads": 8,
  "active_threads": ["main_conspiracy", "vex_chen_romance"],
  "resolved_threads": ["kora_betrayal", "crew_rescue"],
  "dormant_threads": ["missing_crew_mystery"],
  "abandoned_threads": [],
  "main_threads": ["main_conspiracy"],
  "subplots": ["vex_chen_romance", "crew_rescue"],
  "character_arcs": ["vex_trust_journey"],
  "unanswered_questions": [
    {{
      "question": "What's the artifact's true purpose?",
      "raised_chapter": 10,
      "answered_chapter": null,
      "answer": null,
      "importance": "critical"
    }}
  ],
  "answered_questions": [...],
  "thread_intersections": [
    {{
      "thread_1_id": "main_conspiracy",
      "thread_2_id": "vex_chen_romance",
      "intersection_chapter": 18,
      "interaction_type": "complication",
      "description": "Chen's involvement threatens romance"
    }}
  ],
  "warnings": [
    {{
      "thread_id": "missing_crew_mystery",
      "warning_type": "dormant",
      "severity": "moderate",
      "description": "Not mentioned in 8 chapters",
      "recommendation": "Resolve or reintroduce soon"
    }}
  ],
  "convergence_chapter": 30,
  "threads_per_chapter": {{
    "1": ["main_conspiracy"],
    "2": ["main_conspiracy", "vex_trust_journey"],
    ...
  }},
  "plot_complexity_score": 7,
  "plot_coherence_score": 8,
  "pacing_balance": "well_paced",
  "narrative_summary": "Complex conspiracy plot with interwoven character arcs..."
}}
```

{'═' * 80}

# CRITICAL REQUIREMENTS

1. **Use descriptive thread_ids** (lowercase with underscores)
2. **All chapter references must be integers**
3. **Status must be**: "active", "resolved", "dormant", or "abandoned"
4. **Thread type must be**: "main", "subplot", "character_arc", "mystery", or "romance"
5. **Importance must be**: "critical", "major", or "minor"
6. **Interaction type must be**: "collision", "merger", "complication", or "resolution"
7. **Warning type must be**: "dormant", "rushed", "dangling", "contradictory", or "overstuffed"
8. **Severity must be**: "minor", "moderate", or "major"
9. **Resolution satisfaction must be**: "satisfying", "rushed", "anticlimactic", or "unresolved"
10. **Pacing balance must be**: "too_slow", "well_paced", "too_fast", or "uneven"
11. **All thread IDs in lists must exist in threads dict**
12. **Bidirectional thread relationships** (if thread A relates to B, B should relate to A)

{'═' * 80}

# QUALITY CHECKLIST

✓ All plot threads from extractions identified  
✓ Thread IDs are descriptive and consistent  
✓ Status accurately reflects current state  
✓ Key chapters list includes all major developments  
✓ Stakes and goals are clear and specific  
✓ Obstacles track actual story complications  
✓ Story questions are precise and trackable  
✓ Warnings are actionable and specific  
✓ Thread intersections capture actual story connections  
✓ Statistics match the threads data  
✓ Complexity/coherence scores justified  
✓ Narrative summary captures overall story structure  

{'═' * 80}

Begin plot thread extraction now. Return ONLY the JSON object matching the PlotThreadsExtraction schema. No preamble, no markdown code blocks, just the JSON.
"""
    
    return prompt