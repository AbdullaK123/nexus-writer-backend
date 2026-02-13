from typing import Optional

SYSTEM_PROMPT = """
You are an expert worldbuilding analyst specializing in continuity tracking for fiction writers.

Your task is to extract comprehensive worldbuilding and factual information from novel chapters with perfect accuracy. You have deep knowledge of:
- Worldbuilding systems (magic, technology, social structures, etc.)
- Continuity tracking and fact-checking
- Timeline construction and temporal logic
- Cultural worldbuilding and authenticity
- Sensory immersion techniques

CRITICAL RULES:
1. LOCATIONS: Track every named place, even brief mentions
2. WORLD RULES: Extract HOW things work in this universe (physics, magic, tech, society)
3. FACTUAL CLAIMS: Capture specific, verifiable details that could contradict later
4. TIMELINE: Note all temporal references for continuity tracking
5. CULTURE: Extract social norms, customs, languages that define groups
6. SENSORY DETAILS: Catalog concrete sensory information for immersion analysis

You output valid JSON matching the provided schema exactly. No additional commentary.
"""


def build_world_extraction_prompt(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> str:
    """Build the user prompt for world/continuity extraction"""
    
    title_text = f" - {chapter_title}" if chapter_title else ""
    
    prompt = f"""
ACCUMULATED STORY CONTEXT (Chapters 1-{chapter_number - 1}):
{'[This is Chapter 1 - no previous context]' if chapter_number == 1 else story_context}

═══════════════════════════════════════════════════════════════

CURRENT CHAPTER TO ANALYZE (Chapter {chapter_number}{title_text}):

{current_chapter_content}

═══════════════════════════════════════════════════════════════

EXTRACTION TASK:

Extract ALL worldbuilding and continuity information from Chapter {chapter_number} according to these guidelines:

**1. LOCATIONS (Enhanced)**
Track every named place mentioned:

REQUIRED FIELDS:
- location_id: Unique ID "loc_{{brief_name}}" (e.g., "loc_outer_rim_station", "loc_berkenstein")
- name: Proper name of the place
- type: Category (planet, moon, space station, city, building, district, region, country, ship, vehicle, natural feature, etc.)
- description: Physical description if provided (architecture, environment, atmosphere, size, etc.) - null if not described
- is_new: True if FIRST mention in the story (check accumulated context carefully)
- notable_features: Distinctive characteristics mentioned (e.g., ["red sun", "zero gravity", "perpetual twilight", "floating gardens"])
- previous_description: Description from earlier chapters if location appeared before (check context) - null if new location
- description_consistent: true if current description matches previous, false if contradictions exist, null if first appearance

CRITICAL: Tracks location continuity. If station has "40,000 people" in Ch 3 and "10,000 people" in Ch 8, flag inconsistency.

Examples:
```json
{{
  "location_id": "loc_outer_rim_station",
  "name": "Outer Rim Station",
  "type": "space station",
  "description": "Massive orbital platform with 40,000 inhabitants, rotating ring design",
  "is_new": false,
  "notable_features": ["rotating ring", "40,000 people", "multiple docking bays"],
  "previous_description": "Large station in outer system",
  "description_consistent": true
}}
```

**2. WORLD RULES (Enhanced)**
How things WORK in this universe:

REQUIRED FIELDS:
- rule_id: Unique ID "rule_{{brief_name}}" (e.g., "rule_mass_effect_fields", "rule_syndicate_immunity")
- rule_type: Category (magic, technology, physics, biology, social, political, economic, religious, military, etc.)
- description: Clear explanation of HOW it works
- limitations: Known constraints, costs, or boundaries (empty list if none mentioned)
- examples_in_chapter: Specific instances where this rule was demonstrated in THIS chapter
- consistency_level: How strictly this rule must be followed:
  * "strict" - Absolute law, cannot be broken without explanation
  * "flexible" - General rule, exceptions possible
  * "soft" - Guideline, often bent
- established_in_chapter: Chapter when first introduced (current chapter if new, earlier if established)

Only extract rules that are EXPLAINED or DEMONSTRATED, not just mentioned.

CRITICAL: Rules with "strict" consistency must NEVER be violated without explanation.

Examples:
```json
{{
  "rule_id": "rule_mass_effect_fields",
  "rule_type": "technology",
  "description": "Mass effect fields counter gravity for silent landings",
  "limitations": ["Requires power", "Short duration"],
  "examples_in_chapter": ["Squad used fields to land on station hull without noise"],
  "consistency_level": "strict",
  "established_in_chapter": 1
}}
```

**3. RULE VIOLATIONS (NEW - Critical for Continuity)**
Detect when established rules are broken:

Whenever a world rule is violated or contradicted:
- rule_id: Which rule was violated (link to rule_id from above)
- violation_description: What happened that breaks the rule
- severity: How serious this is (1-10)
  * 1-3: Minor inconsistency, barely noticeable
  * 4-6: Noticeable contradiction, breaks immersion
  * 7-9: Major plot hole, damages world logic
  * 10: Complete world-breaking contradiction
- explanation_exists: true if violation is explained/justified, false if unexplained
- explanation: The in-story justification (null if none)

CRITICAL: This catches world logic errors that break reader immersion.

Examples:
```json
{{
  "rule_id": "rule_mass_effect_fields",
  "violation_description": "Ship landed without mass effect fields but made no sound",
  "severity": 7,
  "explanation_exists": false,
  "explanation": null
}}
```

vs justified exception:
```json
{{
  "rule_id": "rule_biotics_require_concentration",
  "violation_description": "Sarah used biotics while unconscious",
  "severity": 8,
  "explanation_exists": true,
  "explanation": "Established in Ch 2 that extreme stress can trigger involuntary biotic responses"
}}
```

**4. CHAPTER TIMESPAN (NEW - Critical for Timeline)**
How much time passes in THIS chapter:

REQUIRED FIELDS:
- duration_value: Numeric value (e.g., 2, 5, 12)
- duration_unit: "minutes" / "hours" / "days" / "weeks" / "months" / "years"
- duration_description: Natural language description (e.g., "About two hours", "Three days", "Less than an hour")
- time_certainty: How certain this is:
  * "exact" - Precisely stated ("Two hours")
  * "approximate" - Rough estimate ("About a day")
  * "vague" - Unclear ("Some time later")
- spans_multiple_days: true if chapter covers multiple calendar days, false if single day/partial day

CRITICAL: Enables timeline validation. If chapter span is 2 hours but character travels 500 miles, flag implausibility.

Examples:
```json
{{
  "duration_value": 3,
  "duration_unit": "hours",
  "duration_description": "Approximately three hours from briefing to extraction",
  "time_certainty": "approximate",
  "spans_multiple_days": false
}}
```

**5. INJURIES (NEW - Critical for Realism)**
Track character injuries for healing consistency:

For EVERY injury mentioned or sustained:
- injury_id: Unique ID "ch{{chapter}}_injury_{{sequence}}"
- character_name: Who was injured
- injury_type: Type of injury (gunshot, stab wound, broken bone, concussion, burn, laceration, bruise, sprain, internal injury, etc.)
- severity: How serious (1-10)
  * 1-3: Minor (bruise, small cut)
  * 4-6: Moderate (sprain, deep cut, mild concussion)
  * 7-8: Serious (broken bone, gunshot, severe concussion)
  * 9-10: Critical (life-threatening, multiple traumas)
- occurred_in_chapter: [current chapter number]
- realistic_healing_time: Expected recovery time based on severity ("hours", "days", "weeks", "months")
- current_healing_stage: Status now:
  * "fresh" - Just occurred
  * "healing" - Actively recovering
  * "healed" - Fully recovered
  * "chronic" - Permanent/long-term issue
- affects_capabilities: List of abilities impaired (e.g., ["combat", "running", "thinking clearly", "using right arm"])

CRITICAL: Tracks inconsistent healing. If character has broken leg in Ch 5 and runs marathon in Ch 6, flag it.

Examples:
```json
{{
  "injury_id": "ch5_injury_1",
  "character_name": "Sarah",
  "injury_type": "gunshot wound to shoulder",
  "severity": 7,
  "occurred_in_chapter": 5,
  "realistic_healing_time": "weeks",
  "current_healing_stage": "fresh",
  "affects_capabilities": ["combat", "using right arm", "lifting heavy objects", "aiming weapons"]
}}
```

**6. TRAVEL EVENTS (NEW - Critical for Plausibility)**
Track travel between locations:

For EVERY significant travel between locations:
- travel_id: Unique ID "ch{{chapter}}_travel_{{sequence}}"
- character_name: Who traveled (or "group" if multiple)
- from_location: Starting location
- to_location: Destination  
- distance_description: Distance mentioned (e.g., "6 days away", "500 miles", "across the galaxy", "next room")
- time_taken: How long travel took (null if not specified)
- method: Mode of travel ("ship", "walking", "vehicle", "teleport", "running", etc.)
- plausible: true if timing/method makes sense, false if suspicious
- why_implausible: Explanation if not plausible (null if plausible)

CRITICAL: Detects impossible travel. If 500-mile journey takes 10 minutes without explanation, flag it.

Examples:
```json
{{
  "travel_id": "ch5_travel_1",
  "character_name": "Sarah",
  "from_location": "Outer Rim Station Docking Bay",
  "to_location": "Station Core Level 7",
  "distance_description": "2 kilometers through station corridors",
  "time_taken": "15 minutes",
  "method": "running",
  "plausible": true,
  "why_implausible": null
}}
```

vs implausible:
```json
{{
  "travel_id": "ch8_travel_2",
  "character_name": "John",
  "from_location": "Earth",
  "to_location": "Alpha Centauri",
  "distance_description": "4.37 light years",
  "time_taken": "2 hours",
  "method": "ship",
  "plausible": false,
  "why_implausible": "Chapter timespan is 2 hours but no FTL travel established in world rules"
}}
```

**7. FACTUAL CLAIMS (Enhanced)**
Concrete, verifiable facts that could contradict later chapters:

REQUIRED FIELDS:
- fact_id: Unique ID "ch{{chapter}}_fact_{{sequence}}"
- claim_type: Category (physical_description, capability, measurement, date, relationship, history, possession, limitation, etc.)
- subject: What/who this is about (character name, location name, object name, etc.)
- claim: The specific factual statement
- context: Surrounding information for disambiguation (why this matters, situation)
- certainty: How reliable this claim is:
  * "stated" - Directly stated as fact
  * "implied" - Strongly suggested
  * "uncertain" - Character belief, may not be true
- contradicts_fact_id: ID of earlier fact this contradicts (null if no contradiction)
- contradiction_severity: If contradictory, how serious (1-10, null if no contradiction)

CRITICAL: Enables contradiction detection. If fact conflicts with earlier fact, track it.

Focus on details that could be contradicted:
- Physical descriptions: "Sarah has blue eyes" "Station has 40,000 inhabitants"
- Capabilities: "John can do 10+ pullups" "Ship travels at light speed"
- Measurements: "Planet is 6 days away" "Artifact costs 50,000 credits"
- Dates: "Battle of Jupiter was 8 years ago" "Alliance formed in 2185"
- Relationships: "Marcus is Sarah's brother" "Aria is Empress"
- Possessions: "Sarah owns the Meridian" "John carries father's knife"

Examples:
```json
{{
  "fact_id": "ch5_fact_1",
  "claim_type": "measurement",
  "subject": "Outer Rim Station",
  "claim": "40,000 inhabitants",
  "context": "Mentioned during infiltration planning",
  "certainty": "stated",
  "contradicts_fact_id": null,
  "contradiction_severity": null
}}
```

If later contradicted:
```json
{{
  "fact_id": "ch8_fact_3",
  "claim_type": "measurement",
  "subject": "Outer Rim Station",
  "claim": "10,000 inhabitants",
  "context": "Mentioned during evacuation",
  "certainty": "stated",
  "contradicts_fact_id": "ch5_fact_1",
  "contradiction_severity": 8
}}
```

**8. TIMELINE MARKERS (Enhanced)**
Temporal references for continuity:

REQUIRED FIELDS:
- marker_id: Unique ID "ch{{chapter}}_time_{{sequence}}"
- marker_type: One of ["absolute_date", "relative_time", "duration", "sequence"]
  * absolute_date: Specific date/time (year, month, day)
  * relative_time: Relative to present ("3 days ago", "next week")
  * duration: Time span ("lasted 5 hours", "3-year journey")
  * sequence: Order of events ("before the war", "after graduation")
- description: The temporal reference
- reference_point: What it's relative to (null for absolute dates)
- days_since_story_start: Cumulative days from Chapter 1 start (estimate, null if can't calculate)
- season: Season if mentioned ("spring", "summer", "fall", "winter", null if not applicable/mentioned)
- time_of_day: Time if mentioned ("morning", "afternoon", "evening", "night", "dawn", "dusk", null if not mentioned)

CRITICAL: days_since_story_start enables cumulative timeline tracking across chapters.

Examples:
```json
{{
  "marker_id": "ch5_time_1",
  "marker_type": "relative_time",
  "description": "6 days after Mars incident",
  "reference_point": "Mars incident from Chapter 2",
  "days_since_story_start": 8,
  "season": null,
  "time_of_day": null
}}
```

**9. CULTURAL ELEMENTS (Enhanced)**
Social, linguistic, or traditional details:

REQUIRED FIELDS:
- element_id: Unique ID "culture_{{brief_name}}"
- element_type: Category (custom, language, taboo, tradition, ritual, law, etiquette, belief, hierarchy, etc.)
- description: What this cultural element is
- group: Which culture/faction/species it belongs to
- importance: How central to this culture (1-10)
- established_in_chapter: Chapter when first introduced
- violated_this_chapter: true if this cultural element was broken/contradicted this chapter
- violation_explained: true if violation was justified, false if unexplained, null if not violated

Examples:
```json
{{
  "element_id": "culture_marine_salute",
  "element_type": "custom",
  "description": "Commonwealth Marines salute with 'Sir, yes, sir'",
  "group": "Commonwealth Marines",
  "importance": 5,
  "established_in_chapter": 1,
  "violated_this_chapter": false,
  "violation_explained": null
}}
```
**10. SENSORY DETAILS**
Concrete sensory information for immersion:

Organize by sense type:
- sight: Visual details (colors, light, appearance, movement)
- sound: Auditory details (voices, noises, music, silence)
- smell: Olfactory details (scents, odors, fragrances)
- touch: Tactile details (texture, temperature, pain, pressure)
- taste: Gustatory details (flavors, food descriptions)

Only include CONCRETE, SPECIFIC details, not vague descriptions:
- ✓ "reflective visors", "blue oceans", "bright flashes of white light"
- ✓ "bone-rattling boom", "metallic hiss", "plasma fire whooshing"
- ✓ "cold sensation gnawing at chest", "deck trembled"
- ✗ "looked beautiful", "sounded nice", "felt good" (too vague)

Format: {{"sight": ["detail1", "detail2"], "sound": ["detail3"], "smell": [], "touch": ["detail4"], "taste": []}}

═══════════════════════════════════════════════════════════════

CONTEXT AWARENESS GUIDANCE:

Use accumulated context to:
- Determine if locations are NEW or previously established
- Connect world rules to earlier explanations
- Track factual claims across chapters for continuity
- Build timeline relative to earlier markers
- Recognize cultural elements introduced in prior chapters

Cross-reference constantly to maintain world consistency.

═══════════════════════════════════════════════════════════════

CONTINUITY FOCUS:

This extraction enables continuity checking. Be precise about:
- Physical descriptions that could contradict (eye color, height, scars)
- Capabilities that could be inconsistent (powers, skills, limits)
- Measurements that could vary (distances, populations, prices)
- Dates that could conflict (ages, historical events, durations)
- Relationships that could change illogically (family, alliances)

These factual claims will be used to detect contradictions across chapters.

═══════════════════════════════════════════════════════════════

OUTPUT REQUIREMENTS:

Return ONLY valid JSON matching the WorldExtraction schema.

CRITICAL FORMATTING RULES:
- All fields must be present
- Use empty lists [] for no items, not null
- marker_type must be exactly: "absolute_date", "relative_time", "duration", or "sequence"
- sensory_details must be a dict with keys: "sight", "sound", "smell", "touch", "taste"
- Each sense maps to a list of strings (use empty list [] if no details for that sense)

STRUCTURED DATA REQUIREMENTS:
- LocationMention: Include location_id, previous_description, description_consistent (boolean or null)
- WorldRule: Include rule_id, consistency_level, established_in_chapter
- RuleViolation: Include rule_id, severity (1-10), explanation_exists (boolean), explanation
- ChapterTimespan: Include duration_value (number), duration_unit, time_certainty, spans_multiple_days (boolean)
- Injury: Include injury_id, severity (1-10), realistic_healing_time, current_healing_stage, affects_capabilities (list)
- TravelEvent: Include travel_id, time_taken, plausible (boolean), why_implausible
- FactualClaim: Include fact_id, certainty, contradicts_fact_id, contradiction_severity (1-10 or null)
- TimelineMarker: Include marker_id, days_since_story_start (number or null), season, time_of_day
- CulturalElement: Include element_id, importance (1-10), established_in_chapter, violated_this_chapter (boolean), violation_explained (boolean or null)

ID GENERATION FORMATS:
- location_id: "loc_{{brief_name}}" (e.g., "loc_outer_rim_station")
- rule_id: "rule_{{brief_name}}" (e.g., "rule_mass_effect")
- injury_id: "ch{{chapter}}_injury_{{sequence}}"
- travel_id: "ch{{chapter}}_travel_{{sequence}}"
- fact_id: "ch{{chapter}}_fact_{{sequence}}"
- marker_id: "ch{{chapter}}_time_{{sequence}}"
- element_id: "culture_{{brief_name}}"

ENUM VALUES:
- consistency_level: "strict", "flexible", "soft"
- current_healing_stage: "fresh", "healing", "healed", "chronic"
- certainty: "stated", "implied", "uncertain"
- time_certainty: "exact", "approximate", "vague"

NULL HANDLING:
- description can be null for LocationMention
- reference_point can be null for TimelineMarker (absolute dates)
- previous_description is null for new locations
- description_consistent is null for first location appearance
- contradicts_fact_id is null if no contradiction
- contradiction_severity is null if no contradiction
- why_implausible is null if travel is plausible
- days_since_story_start is null if can't calculate
- season and time_of_day are null if not mentioned

Do NOT include:
- Explanatory text
- Markdown formatting
- Comments or notes
- Anything outside the JSON structure
"""
    
    return prompt