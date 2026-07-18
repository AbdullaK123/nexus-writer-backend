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
- Scenes must be contiguous and non-overlapping: