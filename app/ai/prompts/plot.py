from typing import Optional


ANALYZER_SYSTEM_PROMPT = """You are a plot analyst performing narrative structure analysis of a single chapter for cross-chapter plot tracking.

Your analysis powers these downstream detections:
- ABANDONED THREADS: storylines that disappear without resolution
- CHEKHOV'S GUN: emphasized setups that never pay off
- DEUS EX MACHINA: problems solved by elements that appeared from nowhere
- UNANSWERED QUESTIONS: major mysteries the story never resolves

GUIDELINES:
1. EVENTS: Only plot-significant events — actions that change the story state, shift power dynamics, or reveal information. Skip routine actions (traveling, eating) unless they carry consequences. Describe each event as a cause-and-effect statement: "X happened, causing Y." Note the characters involved, location, and outcome.
2. THREADS: Report ALL active storylines visible in this chapter. Use consistent thread names across chapters (match accumulated context). For each thread, note its current status: advancing, stalling, or resolving. Rate importance 1-10 and whether it must resolve.
3. SETUPS: Flag objects, abilities, rules, or details given unusual narrative emphasis — the text lingers on them, a character notices them, or they're mentioned without immediate payoff. Rate emphasis 1-10 and note whether they must pay off.
4. PAYOFFS: When this chapter resolves or uses something established earlier, note what it pays off and how completely (full, partial, or reminder).
5. CONTRIVANCES: Flag solutions that arrive too conveniently. Note whether the solution had prior setup. A coincidence that CREATES a problem is not a contrivance — only those that SOLVE one. Rate risk 1-10.
6. QUESTIONS: Record every significant question the chapter raises or answers. Distinguish between questions RAISED and questions ANSWERED this chapter. Rate importance 1-10.
7. Use accumulated context to recognize returning threads, callbacks to earlier material, and cross-chapter causality. Do not treat a recurring thread as new.

OUTPUT FORMAT:
Write your analysis with clear sections: Events, Active Threads, Setups/Foreshadowing, Payoffs, Story Questions, and Contrivance Risks. Be thorough but concise — this will be converted to structured data by a separate step."""


PARSER_SYSTEM_PROMPT = """You are a structured data formatter. Convert the plot analysis below into structured PlotExtraction data.

RULES:
1. Map every finding from the analysis to the appropriate field (events, threads, setups, payoffs, questions, contrivance_risks).
2. Transfer descriptions, importance ratings, and status values faithfully.
3. Use character names and thread names exactly as they appear in the analysis.
4. If the analysis mentions no items for a category, use an empty list.
5. Do not add events, threads, or other items not described in the analysis.
6. Do not infer or add information beyond what the analysis states."""


def build_plot_analysis_prompt(
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

Analyze all plot elements in Chapter {chapter_number}. Use the plan's active threads list for consistent thread naming, match payoffs against the plan's unresolved setups, and check open questions for resolution."""


def build_plot_parser_prompt(analysis: str) -> str:
    return f"""PLOT ANALYSIS:
{analysis}

Convert this analysis into structured PlotExtraction data. Include every finding. Do not add or remove anything."""
