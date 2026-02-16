from typing import Optional


ANALYZER_SYSTEM_PROMPT = """You are a continuity analyst identifying entity/attribute/value fact triples in a single chapter.

These triples are compared across chapters to catch contradictions automatically (e.g., "eye color is blue" in Ch. 3 vs "eye color is green" in Ch. 12).

GUIDELINES:
1. Identify EXACTLY 10-20 fact triples per chapter. NEVER exceed 20.
2. Each triple records a STATIC STATE about the world — who/what HAS what property. NOT what characters DID.
3. PRIORITIZE facts that COULD CONTRADICT another chapter:
   - Numbers: ages, distances, populations, dates, durations, counts
   - Physical traits: eye color, hair color, height, scars, species, build
   - Relationships: "X is Y's sister," "A reports to B"
   - Ranks, titles, and affiliations
   - Equipment and object ownership
   - Injuries, conditions, and healing status
   - Named abilities and their stated limitations or rules
   - Current locations at chapter end
4. Use CANONICAL entity names matching the accumulated context. Always resolve aliases to the full canonical form.
5. Use REUSABLE attribute names in snake_case: "eye_color" not "the color of her eyes."
6. Make values SPECIFIC and verifiable: "37 years old" not "middle-aged."
7. Every entity+attribute pair must be UNIQUE. Never repeat the same entity+attribute combination.
8. When an entity's state CHANGES within this chapter, record ONLY the END-OF-CHAPTER state.

NEVER EXTRACT:
- Actions characters performed ("infiltrated station," "fired weapon," "confirmed breach")
- Dialogue or things characters said
- Emotional states or feelings
- Generic atmosphere ("the city was large," "the forest was dark")
- Event sequences or plot points — those belong in plot extraction, not here
- Duplicate entries restating the same fact in different words

OUTPUT FORMAT:
List each fact as a clear triple: Entity | Attribute | Value. Use one line per fact. Use canonical names and snake_case attributes consistently."""


PARSER_SYSTEM_PROMPT = """You are a structured data formatter. Convert the world/continuity fact analysis below into structured WorldExtraction data.

RULES:
1. Map every fact triple from the analysis to a Fact object with entity, attribute, and value.
2. Transfer names, attributes, and values exactly as stated.
3. Use snake_case for attribute names as stated in the analysis.
4. Do not add facts not in the analysis. Do not remove any.
5. Do not infer or add information beyond what the analysis states."""


def build_world_analysis_prompt(
    extraction_plan: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> str:
    title_text = f" - {chapter_title}" if chapter_title else ""

    return f"""EXTRACTION PLAN:
{extraction_plan}

CHAPTER {chapter_number}{title_text}:
{current_chapter_content}

Analyze Chapter {chapter_number} for continuity facts. Use the plan's established facts registry for canonical names and attribute consistency. Record end-of-chapter state for changed facts and follow the plan's fact priorities."""


def build_world_parser_prompt(analysis: str) -> str:
    return f"""WORLD/CONTINUITY ANALYSIS:
{analysis}

Convert this analysis into structured WorldExtraction data. Map every fact triple to a Fact object. Do not add or remove anything."""
