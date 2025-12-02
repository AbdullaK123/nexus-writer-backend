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

**1. LOCATIONS**
Track every named place mentioned:

For each location:
- name: Proper name of the place
- type: Category (planet, moon, space station, city, building, district, region, country, ship, vehicle, natural feature, etc.)
- description: Physical description if provided (architecture, environment, atmosphere, size, etc.) - null if not described
- is_new: True if FIRST mention in the story (check accumulated context carefully)
- notable_features: Distinctive characteristics mentioned (e.g., ["red sun", "zero gravity", "perpetual twilight", "floating gardens"])

Examples:
- Outer Rim Station (space station) - is_new: false if mentioned earlier
- Berkenstein (planet) - notable_features: ["blue oceans", "brown continents"]
- Docking Bay 7 (building/area) - part of larger station

**2. WORLD RULES**
How things WORK in this universe:

For each rule system:
- rule_type: Category (magic, technology, physics, biology, social, political, economic, religious, military, etc.)
- description: Clear explanation of HOW it works
- limitations: Known constraints, costs, or boundaries (empty list if none mentioned)
- examples_in_chapter: Specific instances where this rule was demonstrated in THIS chapter

Only extract rules that are EXPLAINED or DEMONSTRATED, not just mentioned.

Examples:
- Type: "technology" | Description: "Mass effect fields counter gravity for silent landings" | Limitations: [] | Examples: ["Squad used mass effect fields to land softly on station hull"]
- Type: "social" | Description: "Syndicate operates outside Coalition jurisdiction" | Limitations: ["Only in certain territories"] | Examples: ["Krios explained Syndicate immunity in Outer Rim"]
- Type: "magic" | Description: "Biotics allow telekinetic manipulation" | Limitations: ["Requires concentration", "Drains stamina"] | Examples: ["John snapped guard's neck with biotics", "Kaidan threw up biotic barrier"]

**3. FACTUAL CLAIMS**
Concrete, verifiable facts that could contradict later chapters:

For each claim:
- claim_type: Category (physical_description, capability, measurement, date, relationship, history, possession, limitation, etc.)
- subject: What/who this is about (character name, location name, object name, etc.)
- claim: The specific factual statement
- context: Surrounding information for disambiguation (why this matters, situation)

Focus on details that could be contradicted:
- Physical descriptions: "Sarah has blue eyes" "The station has 40,000 inhabitants"
- Capabilities: "John can do 10+ pullups" "Ship travels at light speed"
- Measurements: "Planet is 6 days away" "Artifact costs 50,000 credits"
- Dates: "Battle of Jupiter was 8 years ago" "Alliance formed in 2185"
- Relationships: "Marcus is Sarah's brother" "Aria is Empress"
- Possessions: "Sarah owns the Meridian" "John carries his father's knife"

Examples:
- claim_type: "physical_description" | subject: "Elias Zephyr" | claim: "Has one bionic eye glowing blue and facial scars" | context: "First direct appearance in control room"
- claim_type: "measurement" | subject: "Outer Rim Station" | claim: "40,000 inhabitants" | context: "Mentioned during infiltration planning"
- claim_type: "history" | subject: "Elias Zephyr" | claim: "Born on Titan, son died at Gamma-Station during Silent Ones attack" | context: "Explains his motivation for terrorism"

**4. TIMELINE MARKERS**
Temporal references for continuity:

For each marker:
- marker_type: One of ["absolute_date", "relative_time", "duration", "sequence"]
  * absolute_date: Specific date/time (year, month, day)
  * relative_time: Relative to present ("3 days ago", "next week")
  * duration: Time span ("lasted 5 hours", "3-year journey")
  * sequence: Order of events ("before the war", "after graduation")
- description: The temporal reference
- reference_point: What it's relative to (null for absolute dates)

Examples:
- marker_type: "relative_time" | description: "6 days after Mars incident" | reference_point: "Mars incident from earlier chapter"
- marker_type: "sequence" | description: "Before the Battle of Jupiter" | reference_point: "Battle of Jupiter"
- marker_type: "duration" | description: "Commonwealth founded 8 years ago" | reference_point: "Present day in story"
- marker_type: "absolute_date" | description: "Chronometer sync 2345 Zulu" | reference_point: null

**5. CULTURAL ELEMENTS**
Social, linguistic, or traditional details:

For each element:
- element_type: Category (custom, language, taboo, tradition, ritual, law, etiquette, belief, hierarchy, etc.)
- description: What this cultural element is
- group: Which culture/faction/species it belongs to

Examples:
- element_type: "custom" | description: "Commonwealth Marines salute with 'Sir, yes, sir'" | group: "Commonwealth Marines"
- element_type: "philosophy" | description: "Justicar Order teaches 'ill will toward enemy is weakness, not strength'" | group: "Justicar Order"
- element_type: "language" | description: "Latin motto 'We stand together' on Commonwealth ships" | group: "Commonwealth"
- element_type: "taboo" | description: "Never trust a quarian (common saying)" | group: "Human colonists"

**6. SENSORY DETAILS**
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
- All fields must be present
- Use empty lists [] for no items, not null
- marker_type must be exactly: "absolute_date", "relative_time", "duration", or "sequence"
- sensory_details must be a dict with keys: "sight", "sound", "smell", "touch", "taste"
- Each sense maps to a list of strings (use empty list [] if no details for that sense)
- description can be null only for LocationMention.description
- reference_point can be null only for TimelineMarker (when marker_type is "absolute_date")

Do NOT include:
- Explanatory text
- Markdown formatting
- Comments or notes
- Anything outside the JSON structure
"""
    
    return prompt