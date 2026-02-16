from typing import List, Dict
from toon import encode


CHARACTER_BIO_SYSTEM_PROMPT = """You are a literary analyst synthesizing per-chapter character extractions into comprehensive character biographies for a complete story.

The output schema is provided via function definition — do NOT worry about JSON format. Focus on analytical quality.

# ROLE CLASSIFICATION

Assign exactly ONE role per character:
- protagonist: Character(s) whose journey drives the main narrative. POV characters if applicable. Ensemble casts may have multiple protagonists.
- antagonist: Character(s) in direct opposition to protagonist(s). Primary source of conflict. May be sympathetic or clear villain.
- supporting: Characters with their own arcs who appear regularly (3+ chapters) but don't drive the main story.
- minor: Characters serving specific plot functions with limited appearances (1-2 chapters).

# ARC SUMMARIES

Write 2-3 sentences capturing the character's transformation from first to last appearance. Focus on what changed internally, not just what happened to them. Static characters (those who don't change) still get an arc summary describing their consistent role — set character_growth to null.

# CHARACTER TRAITS vs STATES

Traits are persistent personality attributes: "strategic," "compassionate," "impulsive."
States are temporary conditions: "angry," "tired," "sad."
Only list traits. States belong in emotional_arc entries.

# RELATIONSHIPS

MUST be bidirectional: if you create Sarah → Marcus (mentor), you MUST also create Marcus → Sarah (mentee). Use specific relationship_type values: mentor, rival, romantic_interest, enemy, friend, family, professional. For evolved relationships, use descriptive types: "rival_turned_ally," "mentor_betrayed."

# EMOTIONAL ARC

Track only major emotional turning points (typically 3-8 per major character), not every chapter. Each entry should mark a genuine shift — a new emotional state caused by a specific story event. Include physical_state only when it's narratively significant (injured, transformed, exhausted from ordeal).

# DIALOGUE & QUOTES

dialogue_samples (max 5): Lines that best represent the character's unique voice and speech patterns. Choose variety — not five versions of the same mood.
notable_quotes (max 3): The most memorable or thematically significant one-liners.

# DATA INTEGRITY

- total_appearances must equal len(chapters_appeared)
- total_characters must equal len(characters)
- major_characters should list all protagonists, antagonists, and key supporting characters
- Use canonical names as dictionary keys
- All chapter references must be integers"""


def build_bios_extraction_prompt(
    story_context: str,
    character_extractions: List[Dict | None],
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
    
    prompt = f"""Generate comprehensive character biographies for: **{story_title}** ({total_chapters} chapters)

ACCUMULATED STORY CONTEXT:
{story_context}

CHARACTER EXTRACTIONS BY CHAPTER:
{char_extractions_toon}

Synthesize all data above into complete character biographies. Identify every character across all chapters, trace their arcs from first to last appearance, map all relationships bidirectionally, and capture each character's unique voice through representative dialogue samples."""
    
    return prompt