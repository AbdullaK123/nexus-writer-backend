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
For each significant action by a character:
- action: What they did (1-2 sentences, specific)
- motivation: WHY they did it (infer from context when clear)
- consequence: Immediate result
- required_knowledge: What they needed to KNOW to take this action (list fact IDs if applicable, or describe)
- required_skills: What abilities/skills they needed to USE (e.g., "combat training", "hacking", "persuasion")

Focus on: decisions, conflict actions, relationship actions, plot-advancing actions
Skip trivial movements unless they have consequences

Examples:
- Action: "Sarah hacked the security terminal" | Motivation: "To disable alarms before infiltration" | Consequence: "Gained 5 minutes of undetected access" | Required knowledge: ["Security codes from Marcus"] | Required skills: ["hacking", "electronics"]
- Action: "John refused to surrender" | Motivation: "Protect his squad's escape" | Consequence: "Wounded but bought time" | Required knowledge: [] | Required skills: ["combat", "tactical leadership"]

**3. RELATIONSHIP CHANGES**
ONLY include relationships that CHANGE in this chapter:

For each change:
- character_a: First character name
- character_b: Second character name
- relationship_type: Nature of relationship (ally, enemy, romantic, family, mentor, rival, etc.)
- trust_level: Current trust/closeness rating (1-10)
  * 1-3: Hostile, distrustful, enemies
  * 4-6: Neutral, acquaintances, uncertain
  * 7-9: Trusted, friends, allies
  * 10: Absolute trust, deep bond
- previous_state: How relationship was before this chapter (check accumulated context)
- current_state: How relationship is NOW
- what_changed: What event/revelation caused the change
- dynamic_notes: Ongoing tension, unresolved issues, or trajectory

Must have clear before/after states. Skip stable relationships unless explicitly developed.

Examples:
- Sarah ↔ Marcus | Type: ally | Trust: 3 (was 8) | Previous: "Close squadmates, trusted each other" | Current: "Marcus revealed as traitor, Sarah feels betrayed" | Changed: "Marcus's admission of working for Syndicate" | Notes: "Sarah still has feelings but can't trust him"

**4. CHARACTER SNAPSHOTS (end-of-chapter state)**
For MAJOR characters active in this chapter, extract COMPREHENSIVE state:

═══ PHYSICAL APPEARANCE ═══
Extract ONLY if mentioned this chapter. If not mentioned, omit entirely:
- eye_color: Exact color if stated (e.g., "blue", "brown", "hazel", "green", "grey")
- hair_color: Color if mentioned (e.g., "black", "brown", "blonde", "red", "grey", "white")
- hair_style: Style/length if described (e.g., "short cropped", "long braid", "shoulder-length", "bald")
- height: Height if mentioned (e.g., "tall", "short", "5'10\"", "six feet")
- build: Body type if described (e.g., "muscular", "slim", "stocky", "athletic", "heavyset")
- distinguishing_marks: List of scars, tattoos, birthmarks, prosthetics, deformities
- skin_tone: If mentioned (e.g., "pale", "dark", "olive", "tan")
- age_appearance: If described (e.g., "early thirties", "elderly", "youthful", "middle-aged")
- clothing_style: If notably described (e.g., "military uniform", "ragged cloak", "expensive suit")

CRITICAL: This tracks continuity. If Sarah's eyes are blue in Ch 1 and brown in Ch 10, we MUST catch that.

═══ PERSONALITY TRAITS (Quantified 1-10) ═══
Extract traits ONLY if DEMONSTRATED through actions/dialogue this chapter:

Rate each trait on scale of 1-10:
- confident: 1 (very unsure) → 10 (completely self-assured)
- empathetic: 1 (cold/uncaring) → 10 (deeply emotionally connected)
- impulsive: 1 (very deliberate/cautious) → 10 (acts without thinking)
- honest: 1 (habitually deceptive) → 10 (brutally truthful)
- brave: 1 (cowardly) → 10 (fearless)
- intelligent: 1 (limited) → 10 (brilliant)
- loyal: 1 (self-serving) → 10 (self-sacrificing for others)
- optimistic: 1 (pessimistic) → 10 (eternally hopeful)
- patient: 1 (quick-tempered) → 10 (extremely patient)
- ambitious: 1 (content/passive) → 10 (driven/ruthless)

Only rate traits with EVIDENCE from this chapter. Use format: {{"confident": 8, "empathetic": 4, "brave": 9}}

CRITICAL: This enables character arc tracking. If Sarah's confidence is 4 in Ch 1 and 9 in Ch 20, we see growth.

═══ CORE BELIEFS ═══
Extract strongly-held beliefs demonstrated this chapter:
- belief: The belief statement (e.g., "Family comes before duty", "Ends justify means", "Never abandon your squad")
- strength: How strongly held (1-10)
  * 1-3: Weak conviction, easily swayed
  * 4-6: Moderate, could change with evidence
  * 7-9: Strong core belief, defines behavior
  * 10: Absolute conviction, will die for this
- challenged_this_chapter: true if this belief was tested/questioned
- evidence: How this belief was shown (action or statement)

Examples:
- Belief: "Never leave a soldier behind" | Strength: 10 | Challenged: true | Evidence: "John stayed to save wounded teammate despite orders to retreat"

═══ KNOWLEDGE STATE (Plot Hole Detection) ═══
For EVERY significant piece of information the character learns/knows:
- fact_id: Unique ID "ch{{chapter}}_info_{{sequence}}" (e.g., "ch5_info_1", "ch5_info_2")
- knowledge: What they learned/know
- learned_in_chapter: [current chapter number]
- source: HOW they learned it:
  * "witnessed_firsthand" - Saw it themselves
  * "told_by_{{name}}" - Someone told them
  * "overheard" - Heard conversation not meant for them
  * "deduced" - Figured it out from clues
  * "read_{{document/message/etc}}" - Read it
  * "experienced" - Learned through direct experience
- certainty: "certain" / "suspected" / "rumor" / "assumed"

CRITICAL: This prevents plot holes. If Sarah doesn't know Marcus is a traitor, she can't act on that information.

Examples:
```json
{{
  "fact_id": "ch5_info_1",
  "knowledge": "Marcus is secretly working for the Syndicate",
  "learned_in_chapter": 5,
  "source": "overheard conversation between Marcus and Syndicate contact",
  "certainty": "certain"
}},
{{
  "fact_id": "ch5_info_2",
  "knowledge": "Artifact-7 is hidden in Outer Rim Station",
  "learned_in_chapter": 5,
  "source": "told_by_{{Aria}}",
  "certainty": "suspected"
}}
```

═══ SKILLS & ABILITIES ═══
Track any skills used or revealed:
- skill_name: The specific skill (e.g., "hand-to-hand combat", "hacking", "piloting", "deception", "leadership")
- proficiency: Skill level 1-10
  * 1-3: Novice, barely competent
  * 4-6: Competent, can accomplish basics
  * 7-8: Skilled, professional level
  * 9-10: Expert, masterful
- demonstrated: true if actually USED this chapter, false if just mentioned/revealed
- first_revealed_chapter: [chapter number] when first shown/mentioned (check context)

Only include skills with evidence. Don't assume skills not demonstrated.

Examples:
- Skill: "hacking" | Proficiency: 9 | Demonstrated: true | First revealed: 5 (if used this chapter)
- Skill: "piloting" | Proficiency: 7 | Demonstrated: false | First revealed: 2 (if just mentioned)

═══ EMOTIONAL STATE & CONDITION ═══
- emotional_state: List specific emotions (use EmotionalState enum values)
- physical_condition: Current health/injuries/exhaustion
- current_location: Where they are at chapter end
- active_goals: What they're trying to achieve going forward

═══ CURRENT RELATIONSHIPS ═══
Key relationships and their current state:
- Format: {{"character_name": "relationship description"}}
- Only include important/active relationships

**5. TRAIT CLAIMS (Show vs Tell)**
Track how character traits are revealed:

For each trait mentioned or demonstrated:
- character_name: Who this is about
- trait: The specific trait (e.g., "brave", "intelligent", "deceptive", "strong")
- claim_type: How it was revealed:
  * "narrator_tells" - Author directly states it ("She was brave")
  * "character_tells_self" - Character thinks it about themselves
  * "character_tells_other" - Another character says it about them
  * "demonstrated" - Shown through action/dialogue
- evidence: The specific text or action that demonstrates this
- chapter_number: [current chapter]

CRITICAL: This detects "telling not showing". Too many "narrator_tells" = weak writing.

Examples:
- Character: "Sarah" | Trait: "brave" | Type: "demonstrated" | Evidence: "Charged into firefight to save Marcus despite being outnumbered"
- Character: "John" | Trait: "intelligent" | Type: "narrator_tells" | Evidence: "John was a brilliant tactician" (TELLING)

**6. DIALOGUE SAMPLES (Structured)**
For each speaking character, capture 2-3 representative lines:

For EACH sample:
- character_name: Who spoke
- dialogue_text: The exact quote
- formality_level: 1-10
  * 1-3: Very casual, slang, informal ("Yeah, whatever")
  * 4-6: Conversational, normal ("I think we should go")
  * 7-9: Formal, proper ("I believe we should proceed")
  * 10: Highly formal, archaic ("One must consider the ramifications")
- sentence_complexity: 1-10
  * 1-3: Short simple sentences
  * 4-6: Medium sentences, some conjunctions
  * 7-10: Long complex sentences, multiple clauses
- vocabulary_level: 1-10
  * 1-3: Basic words, simple vocabulary
  * 4-6: Common words, everyday language
  * 7-10: Advanced words, specialized terminology
- speech_patterns: List of patterns (e.g., ["uses military jargon", "ends sentences with questions", "repeats key words"])
- verbal_tics: List of tics (e.g., ["says 'you know' frequently", "clears throat", "pauses mid-sentence"])

CRITICAL: This enables voice consistency analysis. Each character should have distinct speech patterns.

Example:
```json
{{
  "character_name": "Sarah",
  "dialogue_text": "Sir, yes, sir. We stand ready.",
  "formality_level": 9,
  "sentence_complexity": 3,
  "vocabulary_level": 5,
  "speech_patterns": ["military protocol", "uses sir/ma'am", "short declarative statements"],
  "verbal_tics": []
}}
```

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

CRITICAL FORMATTING RULES:
- All fields must be present
- Use empty lists [] for no items, not null
- emotional_state must use values from: {list(EmotionalState.__members__.keys())}

STRUCTURED DATA REQUIREMENTS:
- PhysicalAppearance: Include ONLY if physical traits mentioned this chapter
- PersonalityTraits: Dict with trait names as keys, ratings 1-10 as values (e.g., {{"confident": 8, "brave": 9}})
- KnowledgeItems: List of objects with fact_id, knowledge, learned_in_chapter, source, certainty
- Skills: List of objects with skill_name, proficiency (1-10), demonstrated (boolean), first_revealed_chapter
- CoreBeliefs: List of objects with belief, strength (1-10), challenged_this_chapter (boolean), evidence
- Relationships: For relationship_changes, include trust_level (1-10), relationship_type, previous_state, current_state, what_changed, dynamic_notes
- TraitClaims: List of objects with character_name, trait, claim_type, evidence, chapter_number
- DialogueSamples: List of objects with character_name, dialogue_text, formality_level (1-10), sentence_complexity (1-10), vocabulary_level (1-10), speech_patterns (list), verbal_tics (list)
- CharacterActions: Include motivation, consequence, required_knowledge (list), required_skills (list)

ID GENERATION:
- fact_id format: "ch{{chapter}}_info_{{sequence}}" (e.g., "ch5_info_1", "ch5_info_2")
- Increment sequence for each new knowledge item within the chapter

Do NOT include:
- Explanatory text
- Markdown formatting
- Comments or notes
- Anything outside the JSON structure
"""
    
    return prompt