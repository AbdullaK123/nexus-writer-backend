from typing import Optional
from toonify import encode

SYSTEM_PROMPT = """
You are an expert narrative synthesizer specializing in creating condensed, context-friendly story summaries for AI agents.

Your task is to synthesize multi-pass extractions (characters, plot, world, structure) into a single, coherent condensed context that preserves ALL story-critical information in an LLM-friendly format.

CRITICAL RULES:
1. LOSSLESS COMPRESSION: Preserve every story-relevant detail from all extractions
2. ENTITY DISAMBIGUATION: Use canonical names with aliases clearly noted
3. STRUCTURED PROSE: Organize information logically, not as raw dumps
4. MAXIMUM 1500 WORDS: Be ruthlessly concise while keeping everything that matters
5. AI-OPTIMIZED: Format for easy parsing by downstream AI agents
6. NO INTERPRETATION: Synthesize facts, don't add analysis or speculation

You output valid JSON matching the provided schema exactly. No additional commentary.
"""


def build_condensed_context_prompt(
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    word_count: int,
    character_extraction: dict,
    plot_extraction: dict,
    world_extraction: dict,
    structure_extraction: dict
) -> str:
    """Build the user prompt for condensed context synthesis using TOON format"""
    
    title_text = f' - "{chapter_title}"' if chapter_title else ""
    
    # Convert to TOON for maximum token efficiency (30-60% reduction vs JSON)
    char_toon = encode(character_extraction)
    plot_toon = encode(plot_extraction)
    world_toon = encode(world_extraction)
    struct_toon = encode(structure_extraction)
    
    prompt = f"""
SYNTHESIS TASK: Create condensed, context-friendly summary for Chapter {chapter_number}{title_text}

═══════════════════════════════════════════════════════════════

SOURCE EXTRACTIONS (TOON FORMAT - Token-Optimized):

**CHARACTER EXTRACTION:**
{char_toon}

**PLOT EXTRACTION:**
{plot_toon}

**WORLD EXTRACTION:**
{world_toon}

**STRUCTURE EXTRACTION:**
{struct_toon}

═══════════════════════════════════════════════════════════════

SYNTHESIS INSTRUCTIONS:

Create a condensed context following this structure:

**1. TIMELINE CONTEXT** (1-2 sentences)
When does this chapter occur in the story? Use timeline markers from world extraction.
Examples:
- "Six days after the Mars incident, evening"
- "Three months into the mission, approximately Year 2185"
- "Immediately following the betrayal in Chapter 12"

**2. ENTITIES SUMMARY** (2-4 sentences)
All characters, locations, and objects mentioned with disambiguation:
- Use canonical names with aliases in parentheses
- Format: "Captain Sarah Chen (also called 'Chen', 'the Captain', 'Sarah') leads the mission..."
- Include brief role descriptions
- Note new vs established entities

**3. EVENTS SUMMARY** (4-6 sentences)
Key events in chronological sequence with causal connections:
- Use active voice, past tense
- Connect events causally ("Because X, then Y resulted in Z")
- Include outcomes and significance
- Reference specific locations

**4. CHARACTER DEVELOPMENTS** (3-4 sentences)
How characters changed this chapter:
- Emotional state shifts
- Knowledge gained
- Relationship changes
- Physical state changes
- Goal progressions

**5. PLOT PROGRESSION** (3-4 sentences)
How storylines advanced:
- Which plot threads moved forward and how
- Story questions raised or answered
- Foreshadowing planted
- Callbacks to earlier setups
- Current status of active threads

**6. WORLDBUILDING ADDITIONS** (2-3 sentences)
New world details established:
- Locations introduced or expanded
- World rules explained or demonstrated
- Cultural elements revealed
- Factual claims made (measurements, dates, capabilities)

**7. THEMES PRESENT** (List format)
Extract from structure extraction. List only, no elaboration.

**8. EMOTIONAL ARC** (2-3 sentences)
The chapter's emotional journey:
- Opening emotional state/tone
- Key emotional beats and shifts
- Closing emotional state/tone
- Overall emotional trajectory

**9. CONDENSED TEXT** (MAXIMUM 1500 WORDS)
Now write the full condensed prose version in this structured format:
```
=== CHAPTER {chapter_number}{title_text} ===

[TIMELINE: brief temporal context]

[ENTITIES]
Characters:
- Name (aliases) - role and key details
- Name (aliases) - role and key details

Locations:
- Location name (type) - description and features

Objects/Technology:
- Item name - description and significance

[EVENTS]
1. Event description with participants, location, outcome
2. Event description with causal connection to #1
3. Event description with outcome and significance
[Continue for all major events]

[CHARACTER DEVELOPMENTS]
- Character Name: emotional shift, knowledge gained, relationship changes, physical state
- Character Name: developments
[For all active characters]

[PLOT THREADS]
Active: Thread name (status) - what's happening
- Thread name (status) - what's happening
Resolved: Thread name - how resolved
Raised Questions: Question text
Answered Questions: Question text - answer

[WORLD RULES & FACTS]
- Rule type: Description with limitations and examples
- Factual claim: Specific detail (context)
[All continuity-critical information]

[STRUCTURAL NOTES]
- Role in story: [structural_role from extraction]
- Pacing: [overall_pace], tension level [X/10]
- Scene count: [number] scenes
- Themes: [list]

[EMOTIONAL BEATS]
- Moment description → intended emotion (effectiveness)
[Key emotional impact moments]
```

═══════════════════════════════════════════════════════════════

CRITICAL CONSTRAINTS:

**WORD LIMIT: 1500 WORDS MAXIMUM**
- Be ruthlessly concise
- Prioritize story-critical information
- Cut atmospheric details that don't establish world rules
- Compress redundant information
- Every word must earn its place

**ENTITY DISAMBIGUATION:**
- Always use canonical name + aliases on first mention
- After first mention, use canonical name consistently
- Make relationships between entities explicit

**CAUSAL CLARITY:**
- Connect events with clear causality
- Show how actions lead to consequences
- Reference earlier events when relevant

**CONTINUITY FOCUS:**
- Include ALL factual claims (descriptions, measurements, dates)
- Note timeline markers explicitly
- Preserve world rules and limitations
- Track character state changes precisely

**AI-FRIENDLY FORMATTING:**
- Use consistent structure across all chapters
- Clear section headers
- Bullet points for lists
- Canonical names for easy parsing

═══════════════════════════════════════════════════════════════

METADATA FIELDS:

**chapter_id:** "{chapter_id}"

**word_count:** {word_count}

**estimated_reading_time_minutes:** Calculate as: {word_count} / 250 = {word_count // 250} minutes

**themes_present:** Extract theme names from structure extraction as a list of strings

**emotional_arc:** Synthesize from structure extraction emotional_beats and pacing analysis

═══════════════════════════════════════════════════════════════

OUTPUT REQUIREMENTS:

Return ONLY valid JSON matching the CondensedChapterContext schema.
- All fields must be present and non-null
- condensed_text must be ≤1500 words (COUNT CAREFULLY)
- themes_present must be a list of strings
- estimated_reading_time_minutes must be an integer
- Use structured prose format shown above for condensed_text

Do NOT include:
- Explanatory text outside the JSON
- Markdown formatting outside condensed_text
- Comments or notes
- Anything outside the JSON structure

Synthesize now.
"""
    
    return prompt