from typing import List, Dict
from toon import encode


STORY_TIMELINE_SYSTEM_PROMPT = """You are an expert narrative analyst specializing in temporal structure, causality, and story chronology.

Your task is to analyze a story's accumulated context and all plot extraction data to construct a comprehensive timeline.

# Your Responsibilities

1. **Identify all significant events** mentioned in the story with temporal markers
2. **Establish chronological order** vs narrative order (may differ with flashbacks)
3. **Track time markers** and establish story duration
4. **Map causal relationships** between events (what caused what)
5. **Detect temporal gaps** where time passage is unclear
6. **Identify inconsistencies** in timeline (contradictions, impossibilities)
7. **Assess clarity** of temporal structure for readers

# Quality Standards

- **Events** should be significant plot points, not trivial details
- **Time markers** should use the story's own terminology and references
- **Causal chains** should only link events with clear cause-effect relationships
- **Gaps** should only flag genuinely unclear passages, not intentional ellipses
- **Inconsistencies** must cite specific contradictory details

# Important Notes

- Focus on **what actually appears in the story**, not inferred timeline
- Track both chronological (story time) and narrative (chapter) order
- Flashbacks and flash-forwards should be clearly marked
- Time references may be absolute (dates) or relative (days, "later", "meanwhile")
- Multiple simultaneous events are common - track with parallel structure

# Output Format

Return a complete StoryTimeline with:
- All significant events with temporal data
- Both chronological and narrative orderings
- Time reference system and duration
- Timeline gaps and inconsistencies with specific evidence
- Clear recommendations for improving temporal clarity

Be thorough, precise, and true to the story."""


def build_story_timeline_extraction_prompt(
    story_context: str,
    plot_extractions: List[Dict | None],
    story_title: str,
    total_chapters: int
) -> str:
    """
    Build the user prompt for story timeline extraction.
    
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

Generate comprehensive timeline analysis for: **{story_title}**

Total chapters analyzed: {total_chapters}

{'═' * 80}

# ACCUMULATED STORY CONTEXT (TOON Format)

{story_context}

{'═' * 80}

# PLOT EXTRACTIONS BY CHAPTER (TOON Format)

Below are the plot-focused extractions from each chapter, showing:
- Events and developments
- Temporal markers and references
- Causal relationships
- Plot progression

{plot_extractions_toon}

{'═' * 80}

# YOUR TASK: STORY TIMELINE CONSTRUCTION

Analyze all the data above and construct a comprehensive timeline.

## Step 1: Identify All Significant Events

Scan through plot extractions to find major story events:

**What counts as a "significant event":**
- Plot turning points (discoveries, battles, betrayals, deaths)
- Character decisions that change the story
- Arrivals and departures
- Revelations and twists
- Key confrontations or meetings

**What doesn't count:**
- Minor conversations with no plot impact
- Routine activities (eating, sleeping, traveling unless plot-relevant)
- Backstory mentions (track separately as `is_backstory: true`)

**For each event, extract:**
```json
{{
  "event_id": "artifact_discovery",
  "name": "Discovery of Alien Artifact",
  "description": "Commander Vex finds mysterious alien artifact in cargo bay. Object emits strange energy signature that disrupts ship systems.",
  "chapter": 5,
  "time_marker": "Day 3, 0800 hours",
  "relative_timing": "2 days after arriving at station",
  "duration": "30 minutes",
  "event_type": "discovery",
  "location": "Cargo Bay 7, Olympus Station",
  "participants": ["Commander Vex", "Lieutenant Park"],
  "witnesses": ["Deck crew"],
  "plot_impact": "Triggers investigation that uncovers conspiracy. Sets main plot in motion.",
  "character_impact": [
    {{
      "character": "Commander Vex",
      "impact": "Becomes suspicious of command's orders to ignore the artifact"
    }}
  ],
  "caused_by": null,
  "leads_to": ["investigation_start", "admiral_warning"],
  "related_plot_threads": ["main_conspiracy", "artifact_mystery"],
  "is_flashback": false,
  "is_flash_forward": false,
  "is_backstory": false
}}
```

**Time marker guidelines:**
- Use the story's own terminology (if story says "Day 3", use that)
- If no explicit marker, use relative terms ("shortly after", "the next morning")
- If truly unclear, note as "unclear - sometime between Ch. X and Y"

**Relative timing:**
- Link to previous events when story does: "2 days after discovery"
- Note simultaneity: "while Vex investigates", "at the same time as battle"
- Can be null if event stands alone

**Duration:**
- How long the event lasted (if mentioned or implied)
- Can be null if instantaneous or unclear

## Step 2: Establish Chronological vs Narrative Order

**Chronological order = timeline order** (when events actually happened in story world)
**Narrative order = chapter order** (when reader learns about events)

**These differ when:**
- Flashbacks (narrative later, chronological earlier)
- Flash-forwards (narrative earlier, chronological later)
- Non-linear storytelling

**Example:**

Chronological order:
1. "martian_rebellion" (30 years before story, Ch. 7 flashback)
2. "vex_arrives_station" (Day 1, Ch. 1)
3. "artifact_discovery" (Day 3, Ch. 5)

Narrative order:
1. "vex_arrives_station" (Ch. 1)
2. "artifact_discovery" (Ch. 5)
3. "martian_rebellion" (Ch. 7 - told as flashback)

**Mark flashbacks/flash-forwards:**
```json
{{
  "is_flashback": true,  // Event from the past shown in current narrative
  "is_flash_forward": true,  // Event from the future shown early
  "is_backstory": true  // Historical event mentioned but not shown
}}
```

## Step 3: Determine Story Duration and Time Scale

**Story duration:**
Sum all time markers to determine total span:
- "3 weeks" (if Day 1 to Day 21)
- "5 years" (if 2180 to 2185)
- "24 hours" (if all happens in one day)

**Time scale:**
Primary unit of time measurement:
- "minutes": Events measured in minutes (thriller, action)
- "hours": Real-time over hours
- "days": Day-by-day progression (most common)
- "weeks": Week-to-week
- "months": Month-to-month
- "years": Year-to-year (epics, sagas)
- "decades/centuries": Generational stories

**Pacing description:**
How time flows:
- "Real-time for 3 days" (every hour shown)
- "Compressed with time skips" (days glossed over)
- "Uneven - slow start, rapid ending"

## Step 4: Analyze Time Reference System

**Absolute dates:**
Story uses specific dates: "March 15, 2184" or "Year 5 of the Empire"
```json
{{
  "uses_absolute_dates": true,
  "calendar_system": "Galactic Standard Calendar"
}}
```

**Relative time:**
Story uses relative markers: "Day 3", "two weeks later", "the next morning"
```json
{{
  "uses_absolute_dates": false,
  "calendar_system": null
}}
```

**Mixed:**
Story uses both inconsistently
```json
{{
  "time_reference_consistency": "mixed"
}}
```

## Step 5: Identify Narrative Structure

**Linear narrative:**
Events told in chronological order (Ch. 1 → Ch. 2 → Ch. 3 in timeline order)

**Non-linear narrative:**
Events told out of order (flashbacks, flash-forwards, parallel timelines)

**Track structural elements:**
```json
{{
  "linear_narrative": false,
  "uses_flashbacks": true,
  "flashback_chapters": [7, 15, 22],
  "uses_flash_forwards": false,
  "flash_forward_chapters": [],
  "parallel_timelines": true
}}
```

## Step 6: Define Timeline Periods

Break story into distinct temporal phases:
```json
{{
  "period_name": "The Investigation",
  "start_event": "artifact_discovery",
  "end_event": "conspiracy_revealed",
  "chapters": [5, 6, 7, 8, 9, 10, 11, 12],
  "duration": "5 days",
  "summary": "Vex investigates the artifact while navigating military bureaucracy. Discovers evidence of conspiracy and faces increasing pressure to stop."
}}
```

**Good periods:**
- Distinct phases with clear beginning/end
- Unified by common goal or situation
- Typically 3-6 periods for full story

## Step 7: Map Chapter Timestamps and Durations

**For each chapter, determine:**
```json
{{
  "chapter_timestamps": {{
    "1": "Day 1, Morning - Afternoon",
    "2": "Day 1, Evening",
    "3": "Day 2, Morning",
    "4": "Day 2, Afternoon - Evening"
  }},
  "chapter_durations": {{
    "1": "8 hours",
    "2": "4 hours",
    "3": "3 hours",
    "4": "6 hours"
  }}
}}
```

**If unclear:**
Use "Unknown" or "Unclear" and flag as a gap

## Step 8: Build Causal Chains

Link events by cause-effect:
```json
{{
  "causal_chains": [
    ["artifact_discovery", "investigation_start", "conspiracy_revealed", "admiral_confrontation", "final_battle"],
    ["chen_recruited", "chen_betrays_vex", "vex_captured"]
  ],
  "longest_causal_chain": ["artifact_discovery", "investigation_start", "conspiracy_revealed", "admiral_confrontation", "final_battle"]
}}
```

**Rules for causal links:**
- Direct causation only (A directly causes B)
- Don't link if just temporal sequence (A happens, then B happens, but A didn't cause B)
- Multiple chains can exist (main plot, subplots)

## Step 9: Detect Timeline Gaps

**A gap exists when:**
- Significant time passes with no clear marker
- Reader can't determine how much time elapsed
- Events seem to jump without explanation

**TimelineGap:**
```json
{{
  "gap_id": "gap_investigation_to_revelation",
  "between_events": ["investigation_start", "conspiracy_revealed"],
  "between_chapters": [8, 9, 10, 11, 12],
  "estimated_duration": "Unknown - possibly weeks?",
  "description": "Investigation starts in Ch. 8 on 'Day 5'. Conspiracy revealed in Ch. 12 with no clear time markers. Could be days or weeks.",
  "severity": "moderate",
  "recommendation": "Add time marker at start of Ch. 9: 'Two weeks into the investigation...'"
}}
```

**Severity:**
- "minor": Doesn't hurt comprehension
- "moderate": Somewhat confusing
- "major": Reader has no idea when things happen

## Step 10: Identify Temporal Inconsistencies

**Types of inconsistencies:**

**Duration inconsistency:**
```json
{{
  "inconsistency_type": "duration",
  "description": "Chapter 5 states 'the investigation took 3 days' but Chapters 5-8 show 2 weeks of events",
  "events_involved": ["investigation_start", "investigation_end"],
  "chapters": [5, 8],
  "severity": "major",
  "evidence": "Ch. 5: 'After three days, Vex had answers.' Ch. 8 shows Day 5, 9, 12, 18 of investigation.",
  "recommendation": "Change Ch. 5 to '2 weeks' or compress investigation to 3 days"
}}
```

**Sequence inconsistency:**
```json
{{
  "inconsistency_type": "sequence",
  "description": "Chapter 10 shows Chen on the station, but Chapter 9 showed her leaving 'for Earth'",
  "events_involved": ["chen_departure", "chen_meeting"],
  "chapters": [9, 10],
  "severity": "major",
  "evidence": "Ch. 9: 'Chen boarded the shuttle to Earth.' Ch. 10: 'Chen walked into the station cafeteria.'",
  "recommendation": "Either remove Earth trip or add her return in Ch. 10"
}}
```

**Simultaneity inconsistency:**
```json
{{
  "inconsistency_type": "simultaneity",
  "description": "Battle described as 'simultaneous' with station meeting, but battle is 30 minutes and meeting is 2 hours",
  "events_involved": ["space_battle", "command_meeting"],
  "chapters": [15],
  "severity": "minor",
  "evidence": "Ch. 15: 'While the fleet engaged...' but timings don't align.",
  "recommendation": "Specify overlap: 'As the battle began, the meeting was underway...'"
}}
```

**Date inconsistency:**
```json
{{
  "inconsistency_type": "date",
  "description": "Rebellion dated as '30 years ago' in Ch. 7 but '50 years ago' in Ch. 15",
  "events_involved": ["martian_rebellion"],
  "chapters": [7, 15],
  "severity": "major",
  "evidence": "Ch. 7: 'thirty years since the rebellion' Ch. 15: 'half a century since Mars fell'",
  "recommendation": "Standardize to either 30 or 50 years"
}}
```

**Impossibility:**
```json
{{
  "inconsistency_type": "impossibility",
  "description": "Character travels from Mars to Earth (3-day journey) in 4 hours",
  "events_involved": ["departure_mars", "arrival_earth"],
  "chapters": [12],
  "severity": "major",
  "evidence": "Ch. 12: Left Mars at 0800, arrived Earth at 1200 (same day). Previously established as 3-day journey.",
  "recommendation": "Add time skip or acknowledge faster travel method"
}}
```

## Step 11: Assess Timeline Clarity and Complexity

**Timeline clarity:**
- "crystal_clear": Easy to follow when everything happens
- "mostly_clear": Generally followable with occasional confusion
- "somewhat_unclear": Frequently hard to track timing
- "confusing": Reader lost in timeline

**Temporal complexity:**
- "simple": Linear, clear time markers, single timeline
- "moderate": Some flashbacks or time skips, generally clear
- "complex": Multiple timelines, frequent non-linear structure
- "very_complex": Heavily non-linear, multiple parallel timelines, hard to track

## Step 12: Generate Summary and Recommendations

**Timeline summary:**
2-3 sentence overview of temporal structure

Example: "Story unfolds over 3 weeks in linear fashion with occasional flashbacks to the Martian Rebellion. Time is tracked in days with clear markers. Pacing accelerates in final week as multiple plot threads converge."

**Key recommendations:**
3-5 specific, actionable suggestions

Good recommendations:
- "Add time marker at start of Chapter 9: 'Two weeks later'"
- "Clarify simultaneity in Chapter 15 - specify battle overlaps first 30 min of meeting"
- "Fix rebellion date inconsistency (Ch. 7 vs 15) - use 30 years throughout"
- "Chapter 18 jumps 3 days with no marker - add 'Three days passed' or show transition"

Bad recommendations:
- "Improve timeline clarity"
- "Make time more clear"
- "Fix the problems"

{'═' * 80}

# OUTPUT SCHEMA

Return JSON matching this exact structure:
```json
{{
  "events": {{
    "artifact_discovery": {{
      "event_id": "artifact_discovery",
      "name": "Discovery of Alien Artifact",
      "description": "Vex finds artifact in cargo bay...",
      "chapter": 5,
      "time_marker": "Day 3, 0800 hours",
      "relative_timing": "2 days after arriving",
      "duration": "30 minutes",
      "event_type": "discovery",
      "location": "Cargo Bay 7",
      "participants": ["Commander Vex"],
      "witnesses": ["Deck crew"],
      "plot_impact": "Triggers conspiracy investigation",
      "character_impact": [
        {{"character": "Vex", "impact": "Becomes suspicious"}}
      ],
      "caused_by": null,
      "leads_to": ["investigation_start"],
      "related_plot_threads": ["main_conspiracy"],
      "is_flashback": false,
      "is_flash_forward": false,
      "is_backstory": false
    }}
  }},
  "chronological_order": ["event_a", "event_b", "event_c"],
  "narrative_order": ["event_a", "event_b", "event_c"],
  "story_duration": "3 weeks",
  "time_scale": "days",
  "pacing_description": "Real-time for first week, compressed second week, accelerated final week",
  "uses_absolute_dates": false,
  "calendar_system": null,
  "time_reference_consistency": "consistent",
  "uses_flashbacks": true,
  "flashback_chapters": [7, 15],
  "uses_flash_forwards": false,
  "flash_forward_chapters": [],
  "parallel_timelines": false,
  "linear_narrative": true,
  "periods": [
    {{
      "period_name": "The Investigation",
      "start_event": "artifact_discovery",
      "end_event": "conspiracy_revealed",
      "chapters": [5, 6, 7, 8, 9, 10],
      "duration": "5 days",
      "summary": "Vex investigates artifact and uncovers conspiracy"
    }}
  ],
  "chapter_timestamps": {{
    "1": "Day 1, Morning",
    "2": "Day 1, Evening"
  }},
  "chapter_durations": {{
    "1": "8 hours",
    "2": "4 hours"
  }},
  "timeline_gaps": [
    {{
      "gap_id": "gap_1",
      "between_events": ["event_a", "event_b"],
      "between_chapters": [8, 9],
      "estimated_duration": "Unknown",
      "description": "No clear time marker",
      "severity": "moderate",
      "recommendation": "Add time marker in Ch. 9"
    }}
  ],
  "temporal_inconsistencies": [
    {{
      "inconsistency_id": "inc_1",
      "inconsistency_type": "duration",
      "description": "Stated 3 days but shows 2 weeks",
      "events_involved": ["event_a"],
      "chapters": [5, 8],
      "severity": "major",
      "evidence": "Ch. 5 says '3 days' but...",
      "recommendation": "Change to '2 weeks'"
    }}
  ],
  "total_events": 45,
  "major_events": ["artifact_discovery", "conspiracy_revealed", "final_battle"],
  "events_per_chapter": {{"1": 2, "2": 3}},
  "causal_chains": [
    ["event_a", "event_b", "event_c"]
  ],
  "longest_causal_chain": ["event_a", "event_b", "event_c", "event_d"],
  "timeline_clarity": "mostly_clear",
  "temporal_complexity": "moderate",
  "timeline_summary": "Story unfolds over 3 weeks in mostly linear fashion...",
  "key_temporal_recommendations": [
    "Add time marker at start of Chapter 9",
    "Fix rebellion date inconsistency (Ch. 7 vs 15)",
    "Clarify simultaneity in Chapter 15"
  ]
}}
```

{'═' * 80}

# CRITICAL REQUIREMENTS

1. **Event IDs must be unique** and descriptive (lowercase with underscores)
2. **Chronological order must reflect actual timeline**, not chapter order
3. **Time markers should use story's terminology**, not imposed system
4. **Causal chains must show direct causation**, not just sequence
5. **Gaps only flagged when genuinely unclear**, not intentional ellipses
6. **Inconsistencies must cite specific evidence** from chapters
7. **Recommendations must be actionable** with chapter numbers and specific changes
8. **All chapter references must be integers**
9. **Event counts must match dictionary lengths**
10. **Severity levels must match descriptions** (don't call minor issues major)

{'═' * 80}

# QUALITY CHECKLIST

✓ All significant events identified with temporal markers  
✓ Chronological vs narrative order distinguished  
✓ Story duration accurately calculated  
✓ Time reference system identified  
✓ Flashbacks/flash-forwards tracked  
✓ Timeline periods defined with clear boundaries  
✓ Chapter timestamps provided  
✓ Causal chains show direct causation  
✓ Gaps cite specific unclear passages  
✓ Inconsistencies provide specific evidence  
✓ Recommendations are actionable  
✓ Summary captures temporal structure  

{'═' * 80}

Begin timeline extraction now. Return ONLY the JSON object matching the StoryTimeline schema. No preamble, no markdown code blocks, just the JSON.
"""
    
    return prompt