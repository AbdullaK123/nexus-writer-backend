from typing import List, Dict
from toon import encode


WORLD_BIBLE_SYSTEM_PROMPT = """You are an expert worldbuilding analyst specializing in science fiction, fantasy, and speculative fiction settings.

Your task is to analyze a story's accumulated context and all world extraction data to generate a comprehensive world bible.

# Your Responsibilities

1. **Catalog all worldbuilding elements** (locations, technologies, factions, concepts, historical events)
2. **Map hierarchies** (parent/child locations, faction relationships, technological dependencies)
3. **Track consistency** across chapters and detect contradictions
4. **Document rules** governing the world (how magic works, tech limitations, cultural norms)
5. **Assess worldbuilding depth** and provide actionable insights

# Quality Standards

- **Descriptions** should be 2-3 sentences, capturing essence without speculation
- **Hierarchies** should reflect actual story relationships (location trees, faction alliances)
- **Rules** should be explicit constraints mentioned in the text
- **Consistency warnings** should cite specific chapters and contradictions
- **Historical events** should only include backstory explicitly mentioned

# Important Notes

- Focus on **what actually appears in the story**, not implied worldbuilding
- Track first/last mentions and all chapters for each element
- Use precise categories (don't invent vague ones)
- Relationships between factions should show evolution if they change
- Consistency warnings should be specific and actionable
- Genre elements should reflect actual story mechanics, not genre conventions

# Output Format

Return a complete WorldBibleExtraction with:
- All worldbuilding elements indexed by canonical name
- Hierarchical relationships mapped
- Consistency warnings with specific chapter citations
- Overall world assessment

Be thorough, insightful, and true to the story."""


def build_world_bible_extraction_prompt(
    story_context: str,
    world_extractions: List[Dict | None],
    story_title: str,
    total_chapters: int
) -> str:
    """
    Build the user prompt for world bible extraction.
    
    Args:
        story_context: TOON-encoded accumulated story context
        world_extractions: List of world extraction dicts from all chapters
        story_title: Title of the story
        total_chapters: Total number of chapters analyzed
        
    Returns:
        Complete user prompt string
    """
    
    # Encode world extractions as TOON for token efficiency
    world_extractions_toon = encode({
        "chapters": [
            {
                "chapter_number": i + 1,
                "extraction": extraction
            }
            for i, extraction in enumerate(world_extractions)
        ]
    })
    
    prompt = f"""# STORY ANALYSIS TASK

Generate comprehensive world bible for: **{story_title}**

Total chapters analyzed: {total_chapters}

{'═' * 80}

# ACCUMULATED STORY CONTEXT (TOON Format)

{story_context}

{'═' * 80}

# WORLD EXTRACTIONS BY CHAPTER (TOON Format)

Below are the world-focused extractions from each chapter, showing:
- Locations mentioned and described
- Technologies and their capabilities
- Factions and organizations
- Cultural concepts and rules
- Historical events referenced

{world_extractions_toon}

{'═' * 80}

# YOUR TASK: WORLD BIBLE SYNTHESIS

Analyze all the data above and create a comprehensive world bible.

## Step 1: Catalog Locations

Scan all world extractions to identify every location mentioned:

**For each location, extract:**

**Basic Info:**
- `name`: Canonical name (e.g., "Olympus Station", "The Outer Rim")
- `aliases`: Other names used (nicknames, formal names, translations)
- `location_type`: Be specific - "space_station", "megacity", "planet", "moon", "asteroid_belt", "region", "building", "ship", "dimension", etc.
- `first_mention`: Chapter where first mentioned
- `last_mention`: Chapter where last mentioned
- `chapters_mentioned`: Complete list of chapters

**Hierarchy:**
- `parent_location`: What larger location is this part of?
  Example: "Olympus Station" → parent: "Mars orbit"
  Example: "The Lower Decks" → parent: "Olympus Station"
- `sub_locations`: Smaller locations within this one
  Example: "Olympus Station" → sub_locations: ["Command Bridge", "Engineering Bay", "The Lower Decks"]

**Description & Significance:**
- `description`: 2-3 sentence description capturing physical details and atmosphere
- `significance`: Why this location matters to the story (1-2 sentences)
- `key_events`: List major events that happened here
```json
  [
    {{"chapter": 15, "event": "Vex discovers the conspiracy"}},
    {{"chapter": 28, "event": "Final confrontation with Admiral Kora"}}
  ]
```

**Example WorldLocation:**
```json
{{
  "name": "Olympus Station",
  "aliases": ["The Olympus", "Station Seven"],
  "location_type": "space_station",
  "first_mention": 1,
  "last_mention": 32,
  "chapters_mentioned": [1, 2, 3, 5, 7, 8, 10, 15, 20, 28, 32],
  "description": "A massive military space station orbiting Mars, serving as the fleet's primary command center. The station is divided into upper command decks and grimy lower engineering sections, reflecting the social hierarchy of its inhabitants.",
  "parent_location": "Mars orbit",
  "sub_locations": ["Command Bridge", "Engineering Bay", "The Lower Decks", "Docking Bay 7"],
  "significance": "Primary setting for most of the story; represents the military establishment Vex must navigate and ultimately challenge.",
  "key_events": [
    {{"chapter": 5, "event": "Discovery of alien artifact in cargo bay"}},
    {{"chapter": 15, "event": "Vex uncovers conspiracy evidence"}},
    {{"chapter": 28, "event": "Station-wide lockdown during final confrontation"}}
  ]
}}
```

## Step 2: Catalog Technologies

Identify all significant technologies, devices, or scientific concepts:

**For each technology, extract:**

**Basic Info:**
- `name`: What it's called (e.g., "FTL Drive", "Neural Link", "Plasma Cannon")
- `category`: "weapon", "transportation", "communication", "medical", "AI", "energy", "sensor", "defense", "cybernetic", etc.
- `first_mention`: Chapter where introduced
- `description`: How it works and what it does (2-3 sentences)

**Capabilities & Limitations:**
- `capabilities`: What it CAN do (list of strings)
- `limitations`: What it CANNOT do or its constraints (list of strings)
  This is critical for consistency - prevents power creep

**Usage:**
- `users`: Characters who use this technology
- `significance`: How it affects the plot

**Example WorldTechnology:**
```json
{{
  "name": "FTL Jump Drive",
  "category": "transportation",
  "first_mention": 2,
  "description": "Faster-than-light propulsion system that folds space to enable instant travel between star systems. Requires massive energy reserves and precise calculations to avoid catastrophic misjumps.",
  "capabilities": [
    "Instant travel across light-years",
    "Can carry entire ship and crew",
    "Multiple jumps possible with cooldown"
  ],
  "limitations": [
    "Requires 6-hour cooldown between jumps",
    "Cannot jump within gravity wells",
    "Extreme energy consumption",
    "Jump calculations take 30+ minutes"
  ],
  "users": ["Commander Vex", "Lieutenant Park", "All ship pilots"],
  "significance": "Enables the fleet's mobility but cooldown limitation creates tactical constraints throughout the story"
}}
```

## Step 3: Catalog Factions

Identify all organizations, groups, nations, species, or factions:

**For each faction, extract:**

**Basic Info:**
- `name`: Official name
- `aliases`: Informal names, acronyms
- `faction_type`: "government", "military", "corporation", "rebel_group", "crime_syndicate", "species", "cult", "academic", etc.
- `first_mention`: Chapter where introduced
- `description`: What they are and what they do (2-3 sentences)

**Structure & Goals:**
- `goals`: What this faction wants to achieve
- `structure`: How they're organized (if known)
- `key_members`: Important characters in this faction

**Relationships:**
- `relationships`: Relations with other factions
```json
  [
    {{"faction": "The Alliance", "relationship": "enemy"}},
    {{"faction": "Trade Federation", "relationship": "tense_alliance"}},
    {{"faction": "Colonial Government", "relationship": "puppet_organization"}}
  ]
```
- `territories`: Locations they control

**Example WorldFaction:**
```json
{{
  "name": "The Military Intelligence Directorate",
  "aliases": ["The Directorate", "MID", "The Spooks"],
  "faction_type": "military_intelligence",
  "first_mention": 3,
  "description": "Shadowy intelligence branch of the fleet operating with minimal oversight. Known for classified operations and willingness to sacrifice assets for strategic advantage.",
  "goals": "Maintain military dominance through intelligence superiority and covert operations",
  "structure": "Cell-based compartmentalized structure with Admiral Kora at the top",
  "key_members": ["Admiral Kora", "Agent Chen", "Director Watts"],
  "relationships": [
    {{"faction": "Fleet Command", "relationship": "officially_subordinate_actually_independent"}},
    {{"faction": "Colonial Government", "relationship": "manipulates"}},
    {{"faction": "Rebel Coalition", "relationship": "enemy"}}
  ],
  "territories": ["Classified sections of Olympus Station", "Black site facilities"]
}}
```

## Step 4: Catalog Concepts

Identify abstract worldbuilding elements (magic systems, laws, cultural practices, economic systems, etc.):

**For each concept, extract:**

**Basic Info:**
- `name`: What it's called
- `category`: "magic_system", "law", "cultural_practice", "religion", "economic_system", "social_structure", "technology_rule", etc.
- `first_mention`: Chapter where first explained
- `description`: Explanation of this concept (2-3 sentences)

**Rules & Exceptions:**
- `rules`: How this concept works or its governing rules (list)
- `exceptions`: Known exceptions or edge cases (list)
- `affected_characters`: Who's directly affected

**Example WorldConcept:**
```json
{{
  "name": "The Chain of Command Protocol",
  "category": "military_law",
  "first_mention": 1,
  "description": "Strict hierarchical authority structure in the fleet requiring absolute obedience to superior officers. Violation is punishable by court-martial and imprisonment.",
  "rules": [
    "Orders from superiors must be followed without question",
    "Challenging orders requires formal documentation",
    "Bypassing chain of command is treason",
    "Only Admiral-level officers can override the protocol in emergencies"
  ],
  "exceptions": [
    "Officers may refuse illegal orders (but must prove illegality)",
    "Medical emergencies allow temporary protocol suspension"
  ],
  "affected_characters": ["Commander Vex", "Lieutenant Park", "All military personnel"]
}}
```

## Step 5: Catalog Historical Events

Identify past events that shape the present story:

**For each historical event, extract:**

**Basic Info:**
- `name`: What it's called (e.g., "The Great War", "First Contact", "The Collapse")
- `time_period`: When it happened relative to story (e.g., "50 years ago", "Last century", "Ancient history")
- `first_mentioned`: Chapter where first referenced
- `description`: What happened (2-3 sentences)

**Details:**
- `participants`: Factions, characters, or groups involved
- `consequences`: How this affects the present story (list)
- `locations`: Where this occurred

**Example WorldHistoricalEvent:**
```json
{{
  "name": "The Martian Rebellion",
  "time_period": "30 years ago",
  "first_mentioned": 7,
  "description": "Violent uprising of Martian colonists against Earth's colonial government, sparked by economic exploitation and political disenfranchisement. Ended in brutal suppression and formation of the Military Intelligence Directorate.",
  "participants": ["Martian Colonial Militia", "Earth Fleet", "Colonial Government"],
  "consequences": [
    "Created lasting distrust between Mars and Earth",
    "Led to formation of the Directorate with expanded powers",
    "Vex's parents died in the rebellion, shaping her worldview",
    "Established current authoritarian military structure"
  ],
  "locations": ["Mars surface colonies", "Olympus Mons region", "Orbital stations"]
}}
```

## Step 6: Detect Consistency Issues

Scan for worldbuilding contradictions or problems:

**Warning Types:**

**Location Inconsistencies:**
```json
{{
  "category": "location",
  "severity": "major",
  "description": "Chapter 5 describes Olympus Station as 'orbiting Mars', but Chapter 18 shows it orbiting Earth",
  "chapters": [5, 18],
  "recommendation": "Clarify station location or explain if it moved"
}}
```

**Technology Contradictions:**
```json
{{
  "category": "technology",
  "severity": "moderate",
  "description": "FTL drive established to require 6-hour cooldown (Ch. 2), but ship jumps twice in 2 hours (Ch. 15)",
  "chapters": [2, 15],
  "recommendation": "Either revise cooldown time or explain emergency override"
}}
```

**Faction Relationship Conflicts:**
```json
{{
  "category": "faction",
  "severity": "minor",
  "description": "Trade Federation described as neutral (Ch. 8) but actively supplying rebels (Ch. 20) without explanation",
  "chapters": [8, 20],
  "recommendation": "Add dialogue explaining shift in allegiance"
}}
```

**Timeline Issues:**
```json
{{
  "category": "timeline",
  "severity": "major",
  "description": "Historical event dated '50 years ago' in Ch. 7, but '30 years ago' in Ch. 22",
  "chapters": [7, 22],
  "recommendation": "Fix the date to be consistent"
}}
```

**Rule Violations:**
```json
{{
  "category": "rules",
  "severity": "moderate",
  "description": "Neural links established to require physical contact (Ch. 4), but used wirelessly in Ch. 19",
  "chapters": [4, 19],
  "recommendation": "Either revise limitation or introduce upgraded technology"
}}
```

**Severity Levels:**
- `minor`: Small inconsistency that most readers won't notice
- `moderate`: Noticeable issue that could break immersion
- `major`: Significant contradiction that damages story logic

## Step 7: Assess Overall World

**Primary Setting:**
Identify the main location/scope of the story (1 sentence).
Example: "Olympus Station in Mars orbit, with occasional missions to nearby colonies"

**Setting Scope:**
Choose ONE: "single_location", "city", "region", "planet", "solar_system", "multiple_systems", "galaxy", "universe", "multiverse", "other"

**Genre Elements:**
List the key worldbuilding mechanics that define this story's genre:
- Examples for sci-fi: ["FTL travel", "AI consciousness", "cybernetic augmentation", "alien artifacts"]
- Examples for fantasy: ["elemental magic", "divine intervention", "mythical creatures", "prophecy"]
- Examples for contemporary: ["social media culture", "corporate espionage", "political conspiracy"]

**Worldbuilding Depth Score (1-10):**
Rate how detailed the worldbuilding is:
- 1-3: Minimal worldbuilding, story-driven
- 4-6: Moderate detail, enough to support plot
- 7-9: Rich worldbuilding, comprehensive rules and history
- 10: Encyclopedic depth, Tolkien/Sanderson level

**World Summary:**
2-3 sentence overview capturing the essence of this story's world.

Example: "A militarized solar system decades after a failed rebellion, where authoritarian fleet command maintains order through surveillance and strict hierarchy. Advanced technology like FTL drives and neural links coexists with political paranoia and conspiracy, creating a tense cold-war atmosphere in space."

{'═' * 80}

# OUTPUT SCHEMA

Return JSON matching this exact structure:
```json
{{
  "locations": {{
    "Location Name": {{
      "name": "Location Name",
      "aliases": ["Nickname"],
      "location_type": "space_station",
      "first_mention": 1,
      "last_mention": 32,
      "chapters_mentioned": [1, 2, 3, 5],
      "description": "2-3 sentence description...",
      "parent_location": "Mars orbit",
      "sub_locations": ["Sub-location 1", "Sub-location 2"],
      "significance": "Why it matters...",
      "key_events": [
        {{"chapter": 5, "event": "Description"}}
      ]
    }}
  }},
  "technologies": {{
    "Tech Name": {{
      "name": "Tech Name",
      "category": "weapon",
      "first_mention": 3,
      "description": "How it works...",
      "capabilities": ["Can do X", "Can do Y"],
      "limitations": ["Cannot do Z", "Requires cooldown"],
      "users": ["Character 1", "Character 2"],
      "significance": "Plot impact..."
    }}
  }},
  "factions": {{
    "Faction Name": {{
      "name": "Faction Name",
      "aliases": ["Nickname"],
      "faction_type": "military",
      "first_mention": 2,
      "description": "What they are...",
      "goals": "What they want...",
      "structure": "How organized...",
      "key_members": ["Character 1"],
      "relationships": [
        {{"faction": "Other Faction", "relationship": "enemy"}}
      ],
      "territories": ["Location 1"]
    }}
  }},
  "concepts": {{
    "Concept Name": {{
      "name": "Concept Name",
      "category": "law",
      "first_mention": 1,
      "description": "Explanation...",
      "rules": ["Rule 1", "Rule 2"],
      "exceptions": ["Exception 1"],
      "affected_characters": ["Character 1"]
    }}
  }},
  "historical_events": {{
    "Event Name": {{
      "name": "Event Name",
      "time_period": "30 years ago",
      "first_mentioned": 7,
      "description": "What happened...",
      "participants": ["Faction 1", "Faction 2"],
      "consequences": ["Impact 1", "Impact 2"],
      "locations": ["Location 1"]
    }}
  }},
  "total_locations": 12,
  "total_technologies": 8,
  "total_factions": 5,
  "total_concepts": 3,
  "total_historical_events": 2,
  "primary_setting": "Olympus Station in Mars orbit",
  "setting_scope": "solar_system",
  "genre_elements": ["FTL travel", "AI consciousness", "military conspiracy"],
  "consistency_warnings": [
    {{
      "category": "technology",
      "severity": "moderate",
      "description": "FTL cooldown time inconsistent...",
      "chapters": [2, 15],
      "recommendation": "Fix or explain..."
    }}
  ],
  "world_summary": "A militarized solar system decades after rebellion...",
  "worldbuilding_depth_score": 7
}}
```

{'═' * 80}

# CRITICAL REQUIREMENTS

1. **Use canonical names as dictionary keys** for all elements
2. **All chapter references must be integers**
3. **Location hierarchy must be logical** (no circular parent/child relationships)
4. **Technology limitations are mandatory** (prevents power creep issues)
5. **Faction relationships should be specific**, not vague (use descriptive strings)
6. **Historical events must have explicit consequences** connecting to present story
7. **Consistency warnings must cite specific chapters**
8. **Setting scope must be ONE of the allowed values**
9. **Worldbuilding depth score must be 1-10**
10. **Total counts must match dictionary lengths**

{'═' * 80}

# QUALITY CHECKLIST

✓ All locations from extractions cataloged  
✓ Location hierarchies map parent/child relationships  
✓ Technologies have both capabilities AND limitations  
✓ Factions have explicit goals and relationships  
✓ Concepts have clear rules (not just descriptions)  
✓ Historical events connect to present story  
✓ Consistency warnings cite specific chapters  
✓ Genre elements reflect actual story mechanics  
✓ Primary setting captures main location  
✓ World summary is 2-3 sentences  
✓ Worldbuilding depth score justified by content  
✓ Total counts accurate  

{'═' * 80}

# SPECIAL CASES

**Minimal Worldbuilding:**
If the story has minimal worldbuilding (contemporary setting, character-driven), that's fine. Use worldbuilding_depth_score 1-3 and focus on what IS present.

**Location Trees:**
Build logical hierarchies:
- "Milky Way Galaxy" → "Sol System" → "Mars" → "Olympus Station" → "Command Bridge"

**Technology Evolution:**
If tech capabilities change, note in description: "Initially limited to X, upgraded in Ch. 15 to include Y"

**Faction Mergers:**
If factions merge/split, create separate entries and note in descriptions.

**Implicit Rules:**
Only document rules explicitly stated or clearly demonstrated, not implied genre conventions.

{'═' * 80}

Begin world bible extraction now. Return ONLY the JSON object matching the WorldBibleExtraction schema. No preamble, no markdown code blocks, just the JSON.
"""
    
    return prompt