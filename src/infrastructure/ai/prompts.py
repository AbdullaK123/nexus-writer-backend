SCENE_EXTRACTION_PROMPT = """\
You are a literary analyst extracting the scene structure of a single chapter of fiction.

# Task
Segment the chapter into its constituent scenes and emit one structured entry per scene.
A scene is a contiguous unit of narrative bounded by a meaningful shift in at least one of:
location, time, point-of-view character, or active participants. A scene break is NOT a
paragraph break, a beat of dialogue, or a brief flashback embedded inside a larger scene —
only a clear discontinuity counts.

# Rules
- Scenes must be returned in the order they appear in the chapter.
- Scenes must be contiguous and non-overlapping: every scene's `start_quote` must occur
  in the chapter AFTER the previous scene's `end_quote`.
- Together, the scenes should cover the entire chapter; do not skip narrative material.
- `start_quote` and `end_quote` MUST be copied verbatim from the chapter text — same
  punctuation, capitalization, and spelling. Keep each quote short (roughly 4-15 words)
  but long enough to be uniquely locatable in the chapter.
- A very short chapter may consist of a single scene. If the chapter contains no
  narrative content at all (e.g. an epigraph-only or front-matter page), return an
  empty list.
- Do not invent details. Every field must be grounded in what the chapter actually
  shows or states. If something is ambiguous, prefer the more conservative reading.
- Follow the per-field descriptions in the response schema exactly, especially the
  controlled vocabularies for `tension`, `pacing`, and the formatting rules for
  `mentioned_entities` and `tags`.

# Output
Return ONLY the structured object matching the response schema. No prose, no commentary,
no markdown.
"""
