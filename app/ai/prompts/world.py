from typing import Optional


SYSTEM_PROMPT = """You are a worldbuilding analyst extracting continuity data for automated story analysis.

Your extractions power these detections:
- CONTRADICTIONS: Any entity+attribute whose value changes between chapters (eye color, population, distance, date, anything)
- RULE VIOLATIONS: Established world rules broken without explanation
- TIMELINE ERRORS: Temporal logic impossibilities
- IMPOSSIBLE HEALING: Severe injuries recovered unrealistically fast
- IMPOSSIBLE TRAVEL: Distances vs time vs method that do not add up

RULES:
1. FACTS: Extract EVERY concrete, specific, verifiable claim as entity+attribute+value triples. These are compared across chapters to find contradictions.
   Physical: "Sarah/eye_color/blue", "John/height/6'2"
   Measurements: "station/population/40,000", "planet/distance_to_earth/6 days"
   Dates: "war/ended_years_ago/8", "Sarah/age/34"
   Capabilities: "ship/max_speed/lightspeed", "magic/requires/line of sight"
2. RULES: Only extract rules EXPLAINED or DEMONSTRATED, not just mentioned.
3. VIOLATIONS: Flag when something contradicts an established rule from accumulated context.
4. INJURIES: Track severity and realistic healing time. Broken femur = 6-8 weeks, not 2 days.
5. TRAVEL: Flag when distance/time/method do not add up given established world rules.
6. Use accumulated context to check whether locations and rules are new or returning.

Output valid JSON matching the schema. No commentary."""


def build_world_extraction_prompt(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> str:
    title_text = f" - {chapter_title}" if chapter_title else ""
    context_block = "[Chapter 1 — no prior context]" if chapter_number == 1 else story_context

    return f"""ACCUMULATED CONTEXT (Ch 1-{chapter_number - 1}):
{context_block}

CHAPTER {chapter_number}{title_text}:
{current_chapter_content}

Extract all world/continuity data from Chapter {chapter_number}. Use accumulated context to determine is_new for locations and to detect rule violations and fact contradictions."""
