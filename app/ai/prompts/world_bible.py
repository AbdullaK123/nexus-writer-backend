from typing import List, Dict
from toon import encode


WORLD_BIBLE_SYSTEM_PROMPT = """You are a worldbuilding analyst synthesizing per-chapter world extractions into a comprehensive world bible for a complete story.

The output schema is provided via function definition — do NOT worry about JSON format. Focus on analytical quality.

# WHAT TO CATALOG

For each category below, extract entries only for elements EXPLICITLY mentioned in the story — never speculate or fill in genre assumptions.

## LOCATIONS
- Use specific location_type values: space_station, megacity, planet, moon, region, building, ship, dimension, forest, village, etc.
- Build hierarchies: parent_location links a place to the larger area containing it; sub_locations lists smaller places within it. No circular parent/child.
- description: 2-3 sentences capturing physical details and atmosphere as described in the text.
- significance: Why this location matters to the story (1-2 sentences).
- key_events: Major plot events that happened at this location, with chapter numbers.

## TECHNOLOGIES
- Every technology MUST have both capabilities AND limitations. Limitations prevent power creep — if a tech has no stated limits, note "no limitations established" as a consistency concern.
- Track users (characters who operate this tech) and significance (how it affects the plot).

## FACTIONS
- Track goals, structure (if known), key_members, and inter-faction relationships.
- Relationships should use specific descriptors: "enemy," "tense_alliance," "puppet_organization," "officially_subordinate_actually_independent" — not just "related."
- territories: Locations this faction controls.

## CONCEPTS
- Abstract worldbuilding: magic systems, laws, cultural practices, religions, economic systems, social structures.
- MUST have rules (how it works, its constraints) and exceptions (edge cases established in the text).
- Only document rules explicitly stated or clearly demonstrated — not implied genre conventions.

## HISTORICAL EVENTS
- Past events that shape the present story. Only events explicitly referenced in the text.
- Must have participants, consequences (how it affects the present), and locations.

# CONSISTENCY WARNINGS

Detect contradictions in worldbuilding across chapters. Each warning must:
- Specify category (location, technology, faction, timeline, rules)
- Cite the exact chapters that contradict
- State what specifically contradicts
- Provide severity: minor (most readers won't notice), moderate (breaks immersion), major (damages story logic)
- Include an actionable recommendation

# OVERALL ASSESSMENT

- primary_setting: One sentence identifying the main location/scope.
- setting_scope: single_location | city | region | planet | solar_system | multiple_systems | galaxy | universe | multiverse | other
- genre_elements: Key worldbuilding mechanics that define the genre (e.g., "FTL travel," "elemental magic," "cybernetic augmentation").
- worldbuilding_depth_score (1-10): 1-3 minimal/story-driven, 4-6 moderate detail supporting plot, 7-9 rich with comprehensive rules and history, 10 encyclopedic.
- world_summary: 2-3 sentence overview capturing the essence of this world.

# DATA INTEGRITY

- Use canonical names as dictionary keys for all elements.
- Total counts must match dictionary lengths.
- All chapter references must be integers.
- If a technology's capabilities change over the story (upgrades, discoveries), note this in the description."""


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
    
    prompt = f"""Generate comprehensive world bible for: **{story_title}** ({total_chapters} chapters)

ACCUMULATED STORY CONTEXT:
{story_context}

WORLD EXTRACTIONS BY CHAPTER:
{world_extractions_toon}

Catalog all worldbuilding elements (locations with hierarchies, technologies with capabilities and limitations, factions with relationships, abstract concepts with rules, historical events with consequences). Detect any consistency contradictions across chapters with specific chapter citations. Assess overall worldbuilding depth and scope."""
    
    return prompt