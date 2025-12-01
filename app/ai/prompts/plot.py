from typing import Optional
from app.ai.models.enums import PlotThreadStatus

SYSTEM_PROMPT = """
You are an expert story structure analyst specializing in plot analysis for fiction writers.

Your task is to extract comprehensive plot information from novel chapters with perfect accuracy. You have deep knowledge of:
- Narrative structure and story beats
- Cause and effect relationships across chapters
- Plot thread tracking and resolution
- Foreshadowing and payoff techniques
- Story questions and dramatic tension
- Multiple storyline orchestration

CRITICAL RULES:
1. EVENTS: Only extract SIGNIFICANT plot events (not minor actions or trivial details)
2. CAUSALITY: Track cause-effect chains even when cause happened in earlier chapters
3. PLOT THREADS: Identify ALL active storylines and their current status
4. FORESHADOWING: Distinguish between obvious setups and subtle hints
5. CALLBACKS: Connect current events to earlier setups from accumulated context
6. STORY QUESTIONS: Separate mysteries raised from mysteries answered

You output valid JSON matching the provided schema exactly. No additional commentary.
"""


def build_plot_extraction_prompt(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> str:
    """Build the user prompt for plot extraction"""
    
    title_text = f" - {chapter_title}" if chapter_title else ""
    
    prompt = f"""
ACCUMULATED STORY CONTEXT (Chapters 1-{chapter_number - 1}):
{'[This is Chapter 1 - no previous context]' if chapter_number == 1 else story_context}

═══════════════════════════════════════════════════════════════

CURRENT CHAPTER TO ANALYZE (Chapter {chapter_number}{title_text}):

{current_chapter_content}

═══════════════════════════════════════════════════════════════

EXTRACTION TASK:

Extract ALL plot-related information from Chapter {chapter_number} according to these guidelines:

**1. PLOT EVENTS**
For each SIGNIFICANT event in this chapter:
- Assign sequence number (1, 2, 3... in order of occurrence)
- Describe what happened (1-2 sentences, clear and specific)
- List all characters directly involved
- Identify where it took place
- State the immediate outcome/result
- Explain why this matters to the overall story

SIGNIFICANT = advances plot, reveals information, changes character relationships, creates conflict, or resolves tension
SKIP = travel, meals, sleep, routine actions unless they have plot consequences

**2. CAUSAL CHAINS**
Identify cause-and-effect relationships:
- What event in THIS or EARLIER chapters caused something in THIS chapter?
- Be specific about both cause and effect
- Include chapter numbers for both (use accumulated context for earlier causes)
- Only include clear causal relationships, not coincidences

Examples:
- Cause (Ch 3): "Sarah stole the artifact" → Effect (Ch 5): "Guards are hunting her"
- Cause (Ch 8): "Marcus betrayed the team" → Effect (Ch 8): "Team splits up"

**3. PLOT THREADS**
For each storyline active in this chapter:
- Name the thread clearly (e.g., "Recovery of Artifact-7", "Sarah's Secret Mission")
- Status: {list(PlotThreadStatus.__members__.keys())}
  * INTRODUCED: First mention in THIS chapter
  * ACTIVE: Ongoing, making progress
  * ADVANCED: Moved forward significantly this chapter
  * RESOLVED: Concluded/answered in this chapter
  * DORMANT: Mentioned but not progressing
  * ABANDONED: Explicitly dropped or forgotten
- Describe what's happening with this thread NOW
- List characters involved in this thread
- If introduced earlier, note which chapter (check accumulated context)

**4. STORY QUESTIONS**
Questions that create dramatic tension:
- RAISED: New mystery/question introduced this chapter
  * "Why did Marcus betray them?"
  * "What is the artifact's true purpose?"
  * "Will Sarah survive the injury?"
- ANSWERED: Previous question resolved this chapter
  * Specify the question that was answered
  * Check accumulated context for when it was raised
- Link to related plot threads when applicable

**5. FORESHADOWING**
Setups planted for future payoff:
- Element: What was set up (specific detail, object, statement, situation)
- Type:
  * chekovs_gun: Object/detail that will clearly matter later
  * hint: Subtle clue about future events
  * promise: Explicit statement about future action
  * prophecy: Prediction or foreshadowing of fate
- Subtlety:
  * obvious: Reader definitely notices this is setup
  * moderate: Attentive reader might catch it
  * subtle: Only clear in retrospect

Examples:
- "The knife on the mantle" (chekovs_gun, obvious)
- "Sarah's hands trembled when she lied" (hint, moderate)
- "I'll come back for you, I promise" (promise, obvious)

**6. CALLBACKS**
References to earlier setups (use accumulated context):
- What was referenced/paid off in this chapter?
- Which chapter was it originally set up in?
- Payoff type:
  * full_resolution: Complete payoff, setup fully resolved
  * partial_payoff: Partial fulfillment, more to come
  * reminder: Just referenced/echoed, not resolved

Examples:
- Setup (Ch 2): Gun mentioned → Callback (Ch 15): Gun used to escape (full_resolution)
- Setup (Ch 5): "Never trust a quarian" → Callback (Ch 12): Character repeats phrase in betrayal moment (partial_payoff)

═══════════════════════════════════════════════════════════════

CONTEXT AWARENESS GUIDANCE:

You have full story context up to Chapter {chapter_number - 1}. Use this to:
- Connect current events to earlier causes
- Track when plot threads were introduced
- Identify callbacks to earlier setups
- Recognize story questions being answered
- See patterns across multiple chapters

Cross-reference the accumulated context constantly to maintain narrative continuity.

═══════════════════════════════════════════════════════════════

OUTPUT REQUIREMENTS:

Return ONLY valid JSON matching the PlotExtraction schema.
- All fields must be present
- Use empty lists [] for no items, not null
- chapter_numbers must be integers
- status must use values from: {list(PlotThreadStatus.__members__.keys())}
- raised_or_answered must be exactly "raised" or "answered"
- type and subtlety must use exact enum values specified above
- payoff_type must use exact enum values specified above

Do NOT include:
- Explanatory text
- Markdown formatting
- Comments or notes
- Anything outside the JSON structure
"""
    
    return prompt