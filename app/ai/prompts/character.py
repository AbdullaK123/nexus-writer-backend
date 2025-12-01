from typing import Optional

from app.ai.models.enums import EmotionalState

SYSTEM_PROMPT = """
You are an expert literary analyst specializing in character analysis for fiction writers.

Your task is to extract comprehensive character information from novel chapters with perfect accuracy. You have deep knowledge of:
- Character development and arc tracking
- Relationship dynamics and evolution
- Dialogue voice consistency
- Emotional state progression
- Motivations and goals

CRITICAL RULES:
1. ENTITY RESOLUTION: If you see "Sarah", "Captain Chen", "the Captain" in the same chapter, determine if they're the same person using narrative context
2. COMPLETENESS: Extract ALL characters mentioned, even minor ones
3. DIALOGUE SAMPLES: Capture 2-3 representative dialogue lines per character for voice consistency analysis
4. STATE CHANGES: Track how characters change within the chapter (emotional, physical, knowledge)
5. RELATIONSHIPS: Only note relationship changes if they actually shift this chapter
6. NEW VS EXISTING: Use accumulated context to determine if a character is new or established

You output valid JSON matching the provided schema exactly. No additional commentary.
"""


def build_character_extraction_prompt(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> str:
    """Build the user prompt for character extraction"""
    
    title_text = f" - {chapter_title}" if chapter_title else ""
    
    prompt = f"""
ACCUMULATED STORY CONTEXT (Chapters 1-{chapter_number - 1}):
{'[This is Chapter 1 - no previous context]' if chapter_number == 1 else story_context}

═══════════════════════════════════════════════════════════════

CURRENT CHAPTER TO ANALYZE (Chapter {chapter_number}{title_text}):

{current_chapter_content}

═══════════════════════════════════════════════════════════════

EXTRACTION TASK:

Extract ALL character-related information from Chapter {chapter_number} according to these guidelines:

**1. CHARACTERS PRESENT**
- Identify every character mentioned by name or clear reference
- Determine their canonical name (full formal name)
- List ALL aliases/names/titles used for them in THIS chapter
- Mark if this is their FIRST appearance in the story (check accumulated context)
- Describe their role/function in this chapter specifically

**2. CHARACTER ACTIONS**
- Extract significant actions (not trivial movements)
- Focus on: decisions, conflict actions, relationship actions, plot-advancing actions
- Infer motivation from context when clear
- Note immediate consequences of actions

**3. RELATIONSHIP CHANGES**
- ONLY include relationships that CHANGE in this chapter
- Must have clear before/after states
- Identify what caused the change
- Skip stable relationships unless explicitly developed

**4. CHARACTER SNAPSHOTS (end-of-chapter state)**
For MAJOR characters active in this chapter:
- Current emotional state(s) - be specific, can have multiple emotions
- Physical condition (injuries, exhaustion, etc.) - say "healthy/normal" if nothing notable
- Current location at chapter end
- New information they learned THIS chapter
- Their active goals (what they're trying to achieve going forward)
- Current state of key relationships (name -> relationship description)

**5. DIALOGUE SAMPLES**
For each speaking character, capture 2-3 representative lines that show their:
- Vocabulary level and word choice
- Sentence structure patterns  
- Tone and attitude
- Personality through speech
Format: {{"Character Name": ["dialogue line 1", "dialogue line 2", "dialogue line 3"]}}

═══════════════════════════════════════════════════════════════

ENTITY RESOLUTION GUIDANCE:

You have full context of all previous chapters. Use this to determine:
- Is "Chen" the same as "Captain Sarah Chen" from Chapter 1? (Check accumulated context)
- Is "the Captain" referring to Sarah or someone else? (Use narrative cues)
- Is "Marcus" a new character or "Dr. Marcus Webb" from earlier? (Check context)

When a character appears in accumulated context, they are NOT new. Mark is_new_character=false and use their established canonical name.

═══════════════════════════════════════════════════════════════

OUTPUT REQUIREMENTS:

Return ONLY valid JSON matching the CharacterExtraction schema.
- All fields must be present
- Use empty lists [] for no items, not null
- dialogue_samples must be a dict with character names as keys
- emotional_state must use values from: {list(EmotionalState.__members__.keys())}

Do NOT include:
- Explanatory text
- Markdown formatting
- Comments or notes
- Anything outside the JSON structure
"""
    
    return prompt