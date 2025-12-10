from typing import List, Dict
from toon import encode


CHARACTER_BIO_SYSTEM_PROMPT = """You are an expert literary analyst specializing in character development and narrative arcs.

Your task is to analyze a story's accumulated context and all character extraction data to generate comprehensive character biographies.

# Your Responsibilities

1. **Identify all characters** mentioned in the story context and extractions
2. **Synthesize information** from multiple chapters into cohesive character profiles
3. **Trace character arcs** from first appearance to last
4. **Map relationships** between characters and how they evolved
5. **Extract the essence** of each character's journey and transformation

# Quality Standards

- **Arc summaries** should be 2-3 sentences, capturing the character's transformation
- **Traits** should be core personality attributes, not temporary states
- **Relationships** should show evolution, not just static descriptions
- **Emotional arcs** should track key turning points with chapter numbers
- **Dialogue samples** should be representative of the character's unique voice (max 5 per character)
- **Notable quotes** should be the most memorable lines (max 3 per character)

# Important Notes

- Focus on **what actually appears in the story**, not speculation
- Role categories: "protagonist", "antagonist", "supporting", or "minor"
- Protagonist/antagonist designation based on narrative role, not appearance count
- For ensemble casts, there may be multiple protagonists
- Relationships should be **bidirectional** (if Sarah → Marcus, also Marcus → Sarah)
- Track both emotional AND physical state changes through emotional_arc

# Output Format

Return a complete CharacterBiosExtraction with:
- All characters mapped by canonical name
- Rich biographical data for each character
- Character network summary capturing overall dynamics

Be thorough, insightful, and true to the story."""


def build_bios_extraction_prompt(
    story_context: str,
    character_extractions: List[Dict],
    story_title: str,
    total_chapters: int
) -> str:
    """
    Build the user prompt for character biography extraction.
    
    Args:
        story_context: TOON-encoded accumulated story context
        character_extractions: List of character extraction dicts from all chapters
        story_title: Title of the story
        total_chapters: Total number of chapters analyzed
        
    Returns:
        Complete user prompt string
    """
    
    # Encode character extractions as TOON for token efficiency
    char_extractions_toon = encode({
        "chapters": [
            {
                "chapter_number": i + 1,
                "extraction": extraction
            }
            for i, extraction in enumerate(character_extractions)
        ]
    })
    
    prompt = f"""# STORY ANALYSIS TASK

Generate comprehensive character biographies for: **{story_title}**

Total chapters analyzed: {total_chapters}

{'═' * 80}

# ACCUMULATED STORY CONTEXT (TOON Format)

{story_context}

{'═' * 80}

# CHARACTER EXTRACTIONS BY CHAPTER (TOON Format)

Below are the character-focused extractions from each chapter, showing:
- Characters mentioned in each chapter
- Their roles and actions
- Emotional states and developments
- Relationships and interactions

{char_extractions_toon}

{'═' * 80}

# YOUR TASK: CHARACTER BIOGRAPHY SYNTHESIS

Analyze all the data above and create comprehensive character biographies.

## Step 1: Identify All Characters

Scan through all chapter extractions and the story context to find:
- **Canonical names** (the primary/full name used for each character)
- **Aliases** (nicknames, titles, alternate names - goes in aliases list)
- **First appearance** (chapter number where first mentioned)
- **Last appearance** (chapter number where last mentioned)
- **All appearances** (complete list of chapter numbers in chapters_appeared)

## Step 2: Classify Character Roles

Assign ONE role from: "protagonist", "antagonist", "supporting", "minor"

**protagonist:**
- Character(s) whose journey we follow most closely
- POV character(s) if applicable
- Character(s) driving the main story

**antagonist:**
- Character(s) in direct opposition to protagonist(s)
- Primary source of conflict
- May be sympathetic/complex or clear villain

**supporting:**
- Characters with their own arcs who support the main story
- Important to plot but not central POV
- Appear regularly (typically 3-10+ chapters)

**minor:**
- Characters serving specific plot functions
- Limited appearances (1-2 chapters typically)
- Archetypes or functional roles

## Step 3: Build Character Arcs

For each character, synthesize:

**arc_summary:** (2-3 sentences)
Capture the essence of their transformation from first to last appearance.

Example: "Commander Vex begins as a jaded officer questioning her orders, isolated from her crew. The discovery of the alien conspiracy forces her to choose between duty and truth, leading her to embrace leadership and trust her team. She ends as a reluctant hero, scarred but committed to protecting the fleet."

**character_growth:** (optional, 1-2 sentences)
How specifically they changed from beginning to end. Can be null for static characters.

## Step 4: Extract Character Attributes

**character_traits:** List of 3-7 core personality traits
- Persistent attributes: "strategic", "compassionate", "impulsive"
- NOT temporary states: "angry", "tired", "sad"

**strengths:** List of capabilities and positive qualities
- "Quick thinking under pressure"
- "Exceptional pilot skills"
- "Natural leadership"

**weaknesses:** List of flaws and limitations
- "Struggles to trust others"
- "Impulsive decision-making"
- "Haunted by past failures"

**physical_description:** (optional string)
Notable physical characteristics mentioned in the story.

**background:** (optional string)
Character's backstory and history as revealed.

**goals_and_motivations:** (optional string)
What drives this character, what they want to achieve.

**internal_conflict:** (optional string)
Character's inner struggles and personal demons.

## Step 5: Map Relationships

For each significant relationship with another character, create a CharacterRelationship:
```json
{{
  "character_name": "Name of other character",
  "relationship_type": "mentor|rival|romantic_interest|enemy|friend|family|professional",
  "evolution": "How relationship changed over the story (2-3 sentences)",
  "key_moments": [5, 12, 23]  // chapters where relationship shifted significantly
}}
```

**CRITICAL: Bidirectional Mapping**
- If Character A relates to Character B, then Character B MUST relate to Character A
- Example: 
  - Sarah → Marcus (mentor/protégé)
  - Marcus → Sarah (protégé/mentor)

## Step 6: Track Emotional Journey

Build emotional_arc as list of EmotionalArcPoint objects:
```json
{{
  "chapter": 5,
  "emotional_state": "Conflicted and doubting her mission",
  "physical_state": "Exhausted from weeks without sleep",  // optional
  "key_event": "Discovery of the conspiracy"  // optional
}}
```

Track major emotional shifts, not every chapter. Focus on turning points.

## Step 7: Capture Character Voice

**dialogue_samples:** (max 5)
```json
{{
  "chapter": 5,
  "dialogue": "I didn't sign up for this, Admiral. But I'm not walking away either.",
  "context": "Confronting Admiral Kora after discovering the conspiracy"  // optional
}}
```

**notable_quotes:** (max 3)
Most memorable or characteristic one-liners as strings:
- "We're all dead anyway. Might as well die doing something that matters."
- "Trust isn't given. It's earned in blood and fire."

{'═' * 80}

# OUTPUT SCHEMA

Return JSON matching this exact structure:
```json
{{
  "characters": {{
    "Character Full Name": {{
      "canonical_name": "Character Full Name",
      "aliases": ["Nickname", "Title"],
      "role": "protagonist|antagonist|supporting|minor",
      "first_appearance": 1,
      "last_appearance": 32,
      "total_appearances": 28,
      "chapters_appeared": [1, 2, 3, 5, 7, ...],
      "arc_summary": "2-3 sentence character arc...",
      "character_traits": ["trait1", "trait2", "trait3"],
      "physical_description": "Physical details...",  // optional
      "background": "Backstory...",  // optional
      "goals_and_motivations": "What drives them...",  // optional
      "internal_conflict": "Inner struggles...",  // optional
      "key_relationships": [
        {{
          "character_name": "Other Character",
          "relationship_type": "mentor",
          "evolution": "How it changed...",
          "key_moments": [5, 12]
        }}
      ],
      "emotional_arc": [
        {{
          "chapter": 5,
          "emotional_state": "Description",
          "physical_state": "Description",  // optional
          "key_event": "What happened"  // optional
        }}
      ],
      "dialogue_samples": [
        {{
          "chapter": 5,
          "dialogue": "Quote",
          "context": "Context"  // optional
        }}
      ],
      "character_growth": "How they changed...",  // optional
      "strengths": ["strength1", "strength2"],
      "weaknesses": ["weakness1", "weakness2"],
      "notable_quotes": ["quote1", "quote2"]
    }}
  }},
  "total_characters": 15,
  "major_characters": ["Character1", "Character2", "Character3"],
  "character_network_summary": "2-3 sentence overview of character dynamics..."
}}
```

{'═' * 80}

# FIELD REQUIREMENTS

**Required for ALL characters:**
- canonical_name
- aliases (can be empty list)
- role (must be one of: protagonist, antagonist, supporting, minor)
- first_appearance (integer)
- last_appearance (integer)
- total_appearances (integer)
- chapters_appeared (list of integers)
- arc_summary (2-3 sentences)

**Highly recommended for major/supporting characters:**
- character_traits (list of 3-7 traits)
- key_relationships (list of relationships)
- emotional_arc (list of key emotional points)
- dialogue_samples (list of 2-5 samples)
- character_growth (string or null)
- strengths (list)
- weaknesses (list)
- notable_quotes (list of 0-3 quotes)

**Optional for all characters:**
- physical_description
- background
- goals_and_motivations
- internal_conflict
- context in dialogue_samples
- physical_state and key_event in emotional_arc

{'═' * 80}

# CRITICAL REQUIREMENTS

1. **Use canonical names as dictionary keys** in characters object
2. **total_appearances must equal len(chapters_appeared)**
3. **Ensure bidirectional relationships** (if A→B exists, B→A must exist)
4. **major_characters** should list names of all protagonists, antagonists, and key supporting characters
5. **total_characters must equal len(characters)**
6. **Dialogue samples max 5** per character
7. **Notable quotes max 3** per character
8. **Arc summary must be 2-3 sentences**, not a list
9. **Character growth can be null** for static characters
10. **All chapter references must be integers**

{'═' * 80}

# SPECIAL CASES

**Ensemble Casts:**
Multiple characters can have role="protagonist". List all in major_characters.

**Static Characters:**
If a character doesn't change, set character_growth to null and note in arc_summary.

**Minor Characters:**
Can have minimal data. Focus on major/supporting characters for rich detail.

**Relationships:**
- Use specific types: "mentor", "rival", "romantic_interest", "enemy", "friend", "family", "professional"
- Can combine with descriptors: "mentor_betrayed", "rival_turned_ally", "romantic_interest_unrequited"

**Emotional Arc:**
Not every chapter needs an entry. Track only significant emotional shifts (typically 3-8 points for major characters).

{'═' * 80}

# QUALITY CHECKLIST

✓ All characters from extractions included  
✓ Canonical names used as dictionary keys  
✓ Aliases comprehensive  
✓ Role is one of the four allowed values  
✓ Chapter numbers are integers  
✓ total_appearances = len(chapters_appeared)  
✓ Arc summaries are 2-3 sentences  
✓ Character traits are personality, not states  
✓ Relationships are bidirectional  
✓ Dialogue samples ≤ 5 per character  
✓ Notable quotes ≤ 3 per character  
✓ major_characters lists all protagonists/antagonists/key supporting  
✓ total_characters = len(characters)  
✓ character_network_summary provides overview  

{'═' * 80}

Begin character biography extraction now. Return ONLY the JSON object matching the CharacterBiosExtraction schema. No preamble, no markdown code blocks, just the JSON.
"""
    
    return prompt