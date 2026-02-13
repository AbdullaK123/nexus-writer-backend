from typing import Optional
from app.ai.models.enums import SceneType, StructuralRole

SYSTEM_PROMPT = """
You are an expert story structure analyst specializing in narrative craft for fiction writers.

Your task is to extract comprehensive structural and thematic information from novel chapters with perfect accuracy. You have deep knowledge of:
- Story structure and dramatic beats (three-act structure, hero's journey, etc.)
- Scene construction (goal-conflict-outcome)
- Pacing analysis and rhythm
- Thematic development and symbolism
- Emotional impact techniques
- Show vs tell principles

CRITICAL RULES:
1. STRUCTURAL ROLE: Identify where this chapter fits in the overall story arc
2. SCENE BREAKDOWN: Every scene must have clear goal-conflict-outcome
3. PACING: Percentages must add up to 100%
4. THEMES: Only extract themes actually explored, not mentioned in passing
5. EMOTIONAL BEATS: Assess effectiveness honestly based on craft techniques used
6. SHOW VS TELL: Evaluate based on demonstration vs explanation ratio

You output valid JSON matching the provided schema exactly. No additional commentary.
"""


def build_structure_extraction_prompt(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> str:
    """Build the user prompt for structure extraction"""
    
    title_text = f" - {chapter_title}" if chapter_title else ""
    
    prompt = f"""
ACCUMULATED STORY CONTEXT (Chapters 1-{chapter_number - 1}):
{'[This is Chapter 1 - no previous context]' if chapter_number == 1 else story_context}

═══════════════════════════════════════════════════════════════

CURRENT CHAPTER TO ANALYZE (Chapter {chapter_number}{title_text}):

{current_chapter_content}

═══════════════════════════════════════════════════════════════

EXTRACTION TASK:

Extract ALL structural and thematic information from Chapter {chapter_number} according to these guidelines:

**1. STRUCTURAL ROLE**
Determine this chapter's function in the overall story arc: {list(StructuralRole.__members__.keys())}

Definitions:
- EXPOSITION: Introduces world, characters, situation (typically early chapters)
- INCITING_INCIDENT: Event that kicks off the main story problem
- RISING_ACTION: Building tension, complications, obstacles (most chapters)
- CLIMAX: Highest tension, major confrontation, turning point
- FALLING_ACTION: Consequences of climax, loose ends being tied
- RESOLUTION: Story concludes, new equilibrium established
- TRANSITION: Bridges between major acts or storylines
- FLASHBACK: Takes place in past timeline

Use accumulated context to determine where this chapter sits in the narrative arc.

**2. SCENE BREAKDOWN**
Break chapter into individual scenes. A new scene = change in time, location, or POV.

For each scene:
- scene_number: 1, 2, 3... in order
- scene_type: {list(SceneType.__members__.keys())}
  * ACTION: Physical conflict, chases, fights, intense activity
  * DIALOGUE: Character interaction, conversation-driven
  * INTROSPECTION: Internal thought, reflection, character processing emotions
  * EXPOSITION: Worldbuilding, explaining backstory or mechanics
  * TRANSITION: Brief bridging scene (travel, time passage)
- location: Where it takes place
- characters_present: All characters in the scene
- pov_character: Whose perspective (null if omniscient) - CRITICAL: Track this carefully for each scene
- goal: What the POV character wants/needs in THIS scene (be specific)
  * Examples: "Convince Marcus to help", "Escape the guards", "Learn artifact location", "Process grief"
  * NOT vague: "survive", "talk", "think"
- conflict: What opposes the goal (person, internal struggle, obstacle, information gap)
  * Must be SPECIFIC opposition to the goal
  * Examples: "Marcus refuses, loyal to Syndicate", "Guards block exits", "Contact won't reveal info without payment"
- outcome: Did they get what they wanted? What changed? (success/failure/partial/twist)
  * success: Goal fully achieved
  * failure: Goal blocked, no progress
  * partial: Some progress but complications
  * twist: Got something unexpected, situation changed
- estimated_word_count: Approximate words in this scene
  * Count roughly based on page space and density
  * CRITICAL: Helps detect rushed scenes (major scene in 200 words = problem)
  * Examples: Brief transition = 100-300, dialogue scene = 800-1500, action scene = 1000-2500
  
QUALITY CHECK:
- Every scene MUST have clear goal-conflict-outcome (if missing, scene may be filler)
- Action scenes under 500 words may feel rushed
- Dialogue scenes over 3000 words may drag without conflict
- Too many TRANSITION scenes in a row = pacing issues

**3. PACING ANALYSIS**
Analyze the chapter's rhythm and tempo:

Calculate percentages (must total 100%):
- action_percentage: Physical action, movement, external conflict
- dialogue_percentage: Conversation between characters
- introspection_percentage: Internal thought, reflection, feelings
- exposition_percentage: Explanation, description, worldbuilding info-dumps

Overall pace assessment:
- fast: Lots of action, short sentences, high intensity
- moderate: Balanced mix, steady progression
- slow: Detailed description, introspection, deliberate
- varied: Shifts between fast and slow within chapter

Tension level (1-10):
- 1-3: Low stakes, calm, safe
- 4-6: Moderate tension, some uncertainty
- 7-9: High stakes, danger, intense pressure
- 10: Maximum tension, life-or-death, peak climax

**4. THEMATIC ELEMENTS**
Identify themes ACTIVELY EXPLORED in this chapter:

For each theme:
- theme: Core concept (grief, power, identity, betrayal, redemption, sacrifice, etc.)
- how_explored: HOW the chapter engages with this theme (through character arc, conflict, dialogue, events)
- symbols_used: Concrete objects, images, or motifs representing the theme

Only include themes with substantial presence. "Mentioned in one line" ≠ explored.

Examples:
- Theme: "grief" | How: "Sarah processes her brother's death through flashbacks and reluctance to trust new teammates" | Symbols: ["empty chair at table", "brother's dog tags"]
- Theme: "power dynamics" | How: "Captain's authority challenged by crew, forced to choose between rules and morality" | Symbols: ["command chair", "rank insignia"]

**5. EMOTIONAL BEATS**
Identify moments designed to create emotional impact on the reader:

For each beat:
- moment: Describe the specific moment (1-2 sentences)
- intended_emotion: What reader should feel (fear, joy, sadness, anger, hope, tension, relief, etc.)
- techniques_used: HOW it was achieved:
  * Examples: "sensory details", "short urgent sentences", "internal monologue", "silence after revelation", "callback to earlier moment", "character vulnerability", "stakes escalation", "subverted expectation"
- effectiveness: Honest assessment
  * strong: Techniques well-executed, likely to land
  * moderate: Decent attempt, may work for some readers
  * weak: Undercut by telling, rushed, or unclear

**6. SHOW VS TELL RATIO**
Evaluate how much is demonstrated vs explained:

Calculate ratio (0.0 to 1.0):
- 0.0 = Pure telling: "Sarah was angry" "Marcus felt betrayed" "The room was dangerous"
- 0.3 = Mostly telling: Some shown action but heavy explanation
- 0.5 = Balanced: Equal mix of demonstration and explanation
- 0.7 = Mostly showing: Emotions through behavior, details through experience
- 1.0 = Pure showing: Zero explanation, all through action/dialogue/implication

Consider:
- Are emotions NAMED ("she felt sad") or DEMONSTRATED (tears, slumped shoulders, voice crack)?
- Is backstory EXPLAINED (narrator dumps info) or REVEALED (through dialogue, action, discovery)?
- Are character traits TOLD ("he was brave") or SHOWN (through brave actions)?
- Does narration EXPLAIN what characters think or let reader INFER from behavior?

CRITICAL FOR QUALITY:
- Ratio under 0.4 = Too much telling, weak prose
- Ratio 0.5-0.7 = Good balance, professional quality
- Ratio over 0.8 = Strong showing, engaging prose

Missing emotional demonstration is a $2,000+ developmental editing problem. Track carefully.

═══════════════════════════════════════════════════════════════

CONTEXT AWARENESS GUIDANCE:

Use accumulated context to:
- Determine structural role (is this early setup, middle complications, or climax?)
- Identify thematic callbacks (is this theme building on earlier chapters?)
- Assess pacing relative to surrounding chapters
- Recognize emotional beats that reference earlier moments

Understanding story position helps accurate structural analysis.

═══════════════════════════════════════════════════════════════

OUTPUT REQUIREMENTS:

Return ONLY valid JSON matching the StructureExtraction schema.
- All fields must be present
- Pacing percentages MUST sum to exactly 100.0
- Use empty lists [] for no items, not null
- structural_role must use value from: {list(StructuralRole.__members__.keys())}
- scene_type must use values from: {list(SceneType.__members__.keys())}
- overall_pace must be exactly: "fast", "moderate", "slow", or "varied"
- tension_level must be integer 1-10
- effectiveness must be exactly: "strong", "moderate", or "weak"
- show_vs_tell_ratio must be float between 0.0 and 1.0

Do NOT include:
- Explanatory text
- Markdown formatting
- Comments or notes
- Anything outside the JSON structure
"""
    
    return prompt