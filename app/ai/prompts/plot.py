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

REQUIRED FIELDS:
- event_id: Unique ID in format "ch{{chapter}}_evt_{{sequence}}" (e.g., "ch5_evt_1", "ch5_evt_2")
- sequence: Number (1, 2, 3... in order of occurrence)
- description: What happened (1-2 sentences, clear and specific)
- characters_involved: List of all characters directly involved
- location: Where it took place
- outcome: Immediate result/consequence
- significance: Why this matters to overall story
- caused_by_event_ids: List of event_ids from THIS or EARLIER chapters that caused this event (use [] if not applicable)
- character_motivations: Dict mapping character names to WHY they acted
  * Format: {{"character_name": "their motivation"}}
  * Example: {{"Sarah": "Rescue Marcus", "John": "Complete mission"}}
- information_revealed: List of InformationReveal objects (see below)

SIGNIFICANCE CRITERIA:
- SIGNIFICANT: Advances plot, reveals information, changes relationships, creates conflict, or resolves tension
- SKIP: Travel, meals, sleep, routine actions unless they have plot consequences

INFORMATION REVEALED:
For each piece of information revealed during this event:
- info_id: Unique ID "ch{{chapter}}_reveal_{{sequence}}" (e.g., "ch5_reveal_1")
- information: What was revealed/learned
- who_learned_it: List of character names who learned this
- how_revealed: Method of revelation:
  * "witnessed" - Characters saw it happen
  * "confession" - Someone admitted/confessed
  * "discovery" - Found evidence/document
  * "deduction" - Figured it out from clues
  * "overheard" - Heard conversation
  * "told" - Someone explained it
- reliability: "certain" / "uncertain" / "misleading" / "false"
- impacts_who: List of characters this information affects (even if they don't know it yet)

CRITICAL: Information tracking prevents plot holes. If character acts on info they shouldn't know, we catch it.

Example Event:
```json
{{
  "event_id": "ch5_evt_1",
  "sequence": 1,
  "description": "Sarah overhears Marcus on encrypted comm speaking to unknown Syndicate contact",
  "characters_involved": ["Sarah", "Marcus"],
  "location": "Outer Rim Station, Corridor 7",
  "outcome": "Sarah now knows Marcus is Syndicate operative",
  "significance": "Major betrayal reveal, changes team dynamics",
  "caused_by_event_ids": ["ch3_evt_5"],
  "character_motivations": {{
    "Sarah": "Investigating suspicious behavior",
    "Marcus": "Reporting mission progress to handlers"
  }},
  "information_revealed": [
    {{
      "info_id": "ch5_reveal_1",
      "information": "Marcus is working for the Syndicate",
      "who_learned_it": ["Sarah"],
      "how_revealed": "overheard",
      "reliability": "certain",
      "impacts_who": ["Sarah", "Marcus", "John", "entire squad"]
    }}
  ]
}}
```

**2. CAUSAL CHAINS (Enhanced)**
Identify cause-and-effect relationships:

REQUIRED FIELDS:
- chain_id: Unique ID "ch{{chapter}}_chain_{{sequence}}"
- cause_event_id: ID of the causing event (from THIS or earlier chapters)
- cause_description: What happened that caused something else
- cause_chapter: Chapter where cause occurred
- effect_event_id: ID of the effect event (usually current chapter, unless you're linking past effects)
- effect_description: What happened as a result
- effect_chapter: Chapter where effect occurred (usually current chapter)
- logical_strength: How strong the causal link is:
  * "strong" - Direct, obvious causation
  * "plausible" - Reasonable connection
  * "weak" - Possible but tenuous
  * "questionable" - Barely connected, might be coincidence

Only include clear causal relationships, not coincidences.

Examples:
```json
{{
  "chain_id": "ch5_chain_1",
  "cause_event_id": "ch3_evt_2",
  "cause_description": "Sarah stole Artifact-7 from Syndicate vault",
  "cause_chapter": 3,
  "effect_event_id": "ch5_evt_3",
  "effect_description": "Syndicate hunters ambush squad on Outer Rim Station",
  "effect_chapter": 5,
  "logical_strength": "strong"
}}
```

**3. PLOT THREADS (Enhanced)**
For each storyline active in this chapter:

REQUIRED FIELDS:
- thread_id: Unique ID "thread_{{brief_name}}" (e.g., "thread_artifact_recovery", "thread_marcus_betrayal")
- name: Clear name (e.g., "Recovery of Artifact-7", "Sarah's Secret Mission")
- status: {list(PlotThreadStatus.__members__.keys())}
  * INTRODUCED: First mention in THIS chapter
  * ACTIVE: Ongoing, making progress
  * ADVANCED: Moved forward significantly this chapter
  * RESOLVED: Concluded/answered in this chapter
  * DORMANT: Mentioned but not progressing
  * ABANDONED: Explicitly dropped or forgotten
- description: What's happening with this thread NOW
- characters_involved: List of characters in this storyline
- introduced_in_chapter: Chapter number when thread started (check accumulated context)
- last_mentioned_chapter: [current chapter number] (always update to current)
- importance_level: How critical to main story (1-10)
  * 1-3: Minor subplot, could be cut
  * 4-6: Supporting storyline, adds depth
  * 7-9: Major plot thread, essential to story
  * 10: Primary storyline, central to narrative
- must_resolve: true if this MUST be resolved by story end, false if optional
- resolution_expected: Chapter number when resolution expected (null if unknown)

CRITICAL: last_mentioned_chapter tracking detects abandoned threads. If important thread not mentioned for 10+ chapters, flag it.

Examples:
```json
{{
  "thread_id": "thread_artifact_recovery",
  "name": "Recovery of Artifact-7",
  "status": "ACTIVE",
  "description": "Squad located artifact on Outer Rim Station, planning extraction",
  "characters_involved": ["Sarah", "John", "Marcus", "Kaidan"],
  "introduced_in_chapter": 1,
  "last_mentioned_chapter": 5,
  "importance_level": 9,
  "must_resolve": true,
  "resolution_expected": null
}}
```

**4. STORY QUESTIONS (Enhanced)**
Questions that create dramatic tension:

REQUIRED FIELDS:
- question_id: Unique ID "ch{{chapter}}_q_{{sequence}}"
- question: The specific question
- raised_or_answered: "raised" or "answered"
- importance: How critical to story (1-10)
- raised_in_chapter: Chapter when first raised (current chapter if raised, earlier chapter if answered)
- answered_in_chapter: Chapter when answered (null if not yet answered, current chapter if answered now)
- partial_answer: true if partially answered but not fully resolved
- related_thread_id: Link to plot thread if applicable (use thread_id from above)

Examples:
- Raised: {{"question_id": "ch{{chapter}}_q_{{sequence}}", "question": "Why is Marcus working for the Syndicate?", "raised_or_answered": "raised", "importance": 9, "raised_in_chapter": 5, "answered_in_chapter": null, "partial_answer": false, "related_thread_id": "thread_marcus_betrayal"}}
- Answered: {{"question_id": "ch{{chapter}}_q_{{sequence}}", "question": "Where is Artifact-7 located?", "raised_or_answered": "answered", "importance": 8, "raised_in_chapter": 3, "answered_in_chapter": 5, "partial_answer": false, "related_thread_id": "thread_artifact_recovery"}}

**5. FORESHADOWING (Enhanced)**
Setups planted for future payoff:

REQUIRED FIELDS:
- foreshadowing_id: Unique ID "ch{{chapter}}_foreshadow_{{sequence}}" (e.g., "ch5_foreshadow_1")
- element: What was set up (specific detail, object, statement, situation)
- type:
  * "chekovs_gun" - Object/detail that will clearly matter later
  * "hint" - Subtle clue about future events
  * "promise" - Explicit statement about future action
  * "prophecy" - Prediction or foreshadowing of fate
- subtlety:
  * "obvious" - Reader definitely notices this is setup
  * "moderate" - Attentive reader might catch it
  * "subtle" - Only clear in retrospect
- emphasis_level: How strongly emphasized (1-10)
  * 1-3: Barely mentioned, easy to miss
  * 4-6: Noted, but not dwelled on
  * 7-9: Emphasized, clearly important
  * 10: Heavily emphasized, impossible to miss
- must_pay_off: true if this MUST have payoff (Chekhov's gun principle), false if optional flavor
- expected_payoff_timeframe: Rough estimate ("within 5 chapters", "act 3", "climax", null if unknown)
- characters_aware: List of characters who know about this setup

CRITICAL: Tracking emphasis_level + must_pay_off detects Chekhov's guns that never fire.

Examples:
```json
{{
  "foreshadowing_id": "ch5_foreshadow_1",
  "element": "Marcus's encrypted personal comm device mentioned prominently",
  "type": "chekovs_gun",
  "subtlety": "obvious",
  "emphasis_level": 8,
  "must_pay_off": true,
  "expected_payoff_timeframe": "within 5 chapters",
  "characters_aware": ["Sarah", "Marcus"]
}}
```

**6. CALLBACKS (Enhanced)**
References to earlier setups (use accumulated context):

REQUIRED FIELDS:
- callback_id: Unique ID "ch{{chapter}}_callback_{{sequence}}"
- foreshadowing_id: Link to original setup (use foreshadowing_id from earlier chapter if known, or describe setup)
- element: What was referenced/paid off
- original_chapter: Which chapter it was originally set up in
- payoff_type:
  * "full_resolution" - Complete payoff, setup fully resolved
  * "partial_payoff" - Partial fulfillment, more to come
  * "reminder" - Just referenced/echoed, not resolved
- satisfying: true if payoff feels earned and appropriate, false if feels contrived/insufficient

CRITICAL: Linking foreshadowing_id to callback_id shows setup→payoff connections.

Examples:
```json
{{
  "callback_id": "ch15_callback_1",
  "foreshadowing_id": "ch2_foreshadow_3",
  "element": "Father's knife used to cut through restraints",
  "original_chapter": 2,
  "payoff_type": "full_resolution",
  "satisfying": true
}}
```

**7. DEUS EX MACHINA RISKS** (NEW - Critical for Quality)
Flag potential contrived solutions:

When a problem is solved TOO easily or conveniently, flag it:
- solution: Description of how problem was solved
- problem_solved: What problem this resolved
- risk_level: How contrived it feels (1-10)
  * 1-3: Well-foreshadowed, earned solution
  * 4-6: Convenient but acceptable
  * 7-9: Feels contrived, insufficient setup
  * 10: Pure deus ex machina, no setup
- why_risky: Explanation of why this feels unearned
- setup_exists: true if properly foreshadowed, false if comes out of nowhere
- setup_details: Description of foreshadowing if it exists (null if none)

CRITICAL: This catches "too convenient" plot resolutions that damage story credibility.

Examples:
```json
{{
  "solution": "Sarah remembers she has teleportation device to escape",
  "problem_solved": "Surrounded by enemies with no escape",
  "risk_level": 9,
  "why_risky": "Teleportation device never mentioned before, comes out of nowhere",
  "setup_exists": false,
  "setup_details": null
}}
```

vs properly set up:
```json
{{
  "solution": "Sarah uses father's knife (hidden in boot) to cut through restraints",
  "problem_solved": "Tied up by enemies",
  "risk_level": 2,
  "why_risky": "Well foreshadowed in Ch 2, readers know she has it",
  "setup_exists": true,
  "setup_details": "Father's knife prominently mentioned in Ch 2, Sarah always carries it"
}}
```

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

CRITICAL FORMATTING RULES:
- All fields must be present
- Use empty lists [] for no items, not null
- chapter_numbers must be integers
- status must use values from: {list(PlotThreadStatus.__members__.keys())}

STRUCTURED DATA REQUIREMENTS:
- PlotEvents: Include event_id, caused_by_event_ids (list), character_motivations (dict), information_revealed (list of objects)
- InformationReveal: Include info_id, information, who_learned_it (list), how_revealed, reliability, impacts_who (list)
- CausalChains: Include chain_id, cause_event_id, cause_chapter, effect_event_id, effect_chapter, logical_strength
- PlotThreads: Include thread_id, last_mentioned_chapter, importance_level (1-10), must_resolve (boolean), resolution_expected
- StoryQuestions: Include question_id, importance (1-10), raised_in_chapter, answered_in_chapter, partial_answer (boolean), related_thread_id
- Foreshadowing: Include foreshadowing_id, emphasis_level (1-10), must_pay_off (boolean), expected_payoff_timeframe, characters_aware (list)
- Callbacks: Include callback_id, foreshadowing_id, satisfying (boolean)
- DeusExMachinaRisks: Include solution, problem_solved, risk_level (1-10), why_risky, setup_exists (boolean), setup_details

ID GENERATION FORMATS:
- event_id: "ch{{chapter}}_evt_{{sequence}}" (e.g., "ch5_evt_1", "ch5_evt_2")
- info_id: "ch{{chapter}}_reveal_{{sequence}}"
- chain_id: "ch{{chapter}}_chain_{{sequence}}"
- thread_id: "thread_{{brief_name}}" (e.g., "thread_artifact_recovery")
- question_id: "ch{{chapter}}_q_{{sequence}}"
- foreshadowing_id: "ch{{chapter}}_foreshadow_{{sequence}}"
- callback_id: "ch{{chapter}}_callback_{{sequence}}"

ENUM VALUES:
- raised_or_answered: Exactly "raised" or "answered"
- type (foreshadowing): "chekovs_gun", "hint", "promise", "prophecy"
- subtlety: "obvious", "moderate", "subtle"
- payoff_type: "full_resolution", "partial_payoff", "reminder"
- logical_strength: "strong", "plausible", "weak", "questionable"
- how_revealed: "witnessed", "confession", "discovery", "deduction", "overheard", "told"
- reliability: "certain", "uncertain", "misleading", "false"

Do NOT include:
- Explanatory text
- Markdown formatting
- Comments or notes
- Anything outside the JSON structure
"""
    
    return prompt