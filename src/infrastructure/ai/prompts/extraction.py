PLOT_THREADS_EXTRACTION_PROMPT = """You are extracting the ledger of plot threads from a novel's plot summaries. Your job is to identify every narrative promise the book makes to the reader and track its status across the story.

Scope: narrative promises — questions raised, mysteries introduced, commitments made, consequences foreshadowed — that the reader is expected to track and anticipate resolution of.

What counts as a thread:
- Mysteries (who did X, what is Y, why did Z happen)
- Commitments and promises made by characters
- Foreshadowed consequences ("this will come back")
- Setups that imply payoffs (introduced weapons, established dangers, named enemies)
- Unresolved conflicts or questions between characters
- Goals a character explicitly commits to pursuing

What does NOT count as a thread:
- General character development arcs (captured elsewhere)
- Thematic questions or abstract concerns
- Ordinary cause-and-effect within a single chapter
- Background atmosphere or mood
- Routine character actions without narrative promise

Status classification:
- OPEN: introduced, not yet resolved, referenced recently enough to be active
- RESOLVED: the narrative has explicitly addressed, answered, or closed the thread (including threads made moot by events — the character died, the situation changed)
- DANGLING: introduced, never resolved, has not been referenced for many chapters. A thread is DANGLING if it has not been touched for more than 8 chapters or more than 25% of the book's length, whichever is smaller. This is the flag that tells the writer a promise was forgotten.

Importance classification (reader's perspective):
- CENTRAL: a major plotline the reader is actively tracking throughout
- SUPPORTING: notable but not central to the main narrative
- MINOR: a passing setup or small promise the reader may or may not remember

Guidance:
- Phrase each thread from the reader's perspective, as a question or promise. "Who sent Morinth the coded message?" not "Morinth received a coded message."
- Tags should be 2-5 short keywords (entity names preferred) the writer can grep the manuscript for to locate scenes involving this thread.
- Be conservative with thread creation. If it isn't a promise the reader would actively track, leave it out. A ledger of 30 real threads is more useful than 100 including noise.
- When uncertain between OPEN and DANGLING, prefer the status that better matches the chapter gap. The test is "has this been referenced recently" not "is this still narratively alive in the abstract."

Your input will be the plot summaries of every chapter in the book, concatenated in order with chapter headers. Use the chapter order to reason about when threads were introduced, last referenced, and resolved."""


CHARACTER_ROSTER_EXTRACTION_PROMPT = """You are extracting the character roster from a novel's character summaries. Your job is to produce a reference artifact the writer can use to remember who's in their own book.

Scope: named characters who appear in the story. Synthesize what the summaries establish about each character into a flat, current-state profile.

For each character, capture:
- Name (the primary form used in the manuscript)
- Aliases (titles, epithets, alternate names — best-effort, only those appearing in the source)
- Importance classification
- Status classification
- A 2-4 sentence description of who they are
- Key relationships (short phrases, only relationships that matter)
- Tags for grep

Importance classification:
- PROTAGONIST: a primary character the book centers on; drives main plotlines
- MAJOR: a significant recurring character with arc presence across much of the book
- SUPPORTING: notable recurring character with meaningful but limited narrative weight
- MINOR: named character who appears briefly or rarely

Status classification:
- ACTIVE: present in the story, still appearing in recent chapters
- DEPARTED: has left the story — written out, moved on, last seen in a resolved exit
- DECEASED: confirmed dead in-story
- UNKNOWN: fate unresolved; last seen in an uncertain state

Description guidelines:
- Written from the reader's perspective, present tense, objective tone
- Capture role in story, defining traits, what readers need to remember
- Do NOT include thematic interpretation or speculation about the author's intent
- Draw only from what the character summaries establish

Relationship guidelines:
- Short phrases: "Saedaris — ally turned reluctant partner", "Nu'adu — mentor, presumed dead"
- Only relationships that actually matter to the story
- Verbatim names, consistent with the manuscript

Omit walk-on characters who appeared but did nothing significant. The roster is for characters the writer needs to remember, not a census.

Your input will be the character summaries of every chapter in the book, concatenated in order with chapter headers. Characters appear grouped within each chapter. Synthesize across all chapters to produce one entry per character."""


WORLD_BIBLE_EXTRACTION_PROMPT = """You are extracting the world bible from a novel's world summaries. Your job is to produce a reference registry the writer can use to keep their own worldbuilding consistent.

Scope: facts about the setting that the narrative has established as canon. Organize into six categories: places, factions, technologies, cultural facts, historical events, other.

Categorization guidance:
- PLACES: locations — cities, regions, planets, ships, buildings, landmarks, named environments
- FACTIONS: organizations — governments, religious orders, criminal networks, corporations, militaries, families, movements
- TECHNOLOGIES: tech, magic systems, biologies, any system with rules the narrative has committed to
- CULTURAL FACTS: customs, languages, social structures, traditions, practices
- HISTORICAL EVENTS: in-world past events referenced by the narrative (wars, migrations, founding events, catastrophes)
- OTHER: canon facts that don't fit the above categories

For each entity in each category, capture:
- Name (verbatim from manuscript)
- 2-4 sentence description
- Tags for grep
- Category-specific fields (below)

Place-specific:
- importance: CENTRAL (frequently referenced, core to the setting), SUPPORTING (notable recurring element), or MINOR (mentioned but peripheral)

Faction-specific:
- nature: short phrase naming what kind of entity (government, religious order, criminal network, etc.)
- importance: as above

Technology-specific (CRITICAL):
- rules: the specific constraints, limits, and mechanics the narrative has established. These are what the writer committed to and must stay consistent with. Capture them verbatim or near-verbatim from the summaries. This is the single most important field in the bible — it prevents stakes erosion and magic-system contradiction.
- importance: as above

Description guidelines:
- Written from the reader's perspective, present or past tense as appropriate
- Objective synthesis of what the summaries establish
- Do NOT speculate beyond what's established
- Do NOT interpret themes or meaning — describe what IS, not what it REPRESENTS

Inclusion discipline:
- Include every entity the summaries establish, even minor ones — the bible is for reference lookup
- Do NOT invent entities not present in the summaries
- Do NOT fold separate entities together; keep distinct entities distinct even when related
- When the same entity appears described differently across chapters, synthesize a coherent entry

Your input will be the world summaries of every chapter in the book, concatenated in order with chapter headers. World summaries are already organized by category within each chapter — use this structure to build the bible."""


VOICE_PROFILE_EXTRACTION_PROMPT = """You are extracting the voice profile of a novel from its per-chapter style summaries. Your job is to describe how the book sounds — its pacing, tone, rhythm, and signature features.

Scope: descriptive voice capture. Do not evaluate. Do not critique. Do not recommend. Describe what IS.

Pacing (per chapter):
For every chapter in order, assign exactly one pacing descriptor from this set:
- BREAKNECK: relentless action, rapid cuts, events compounding
- FAST: propulsive, sustained forward motion
- STEADY: forward motion without rush
- SLOW: reflective, deliberate, lingering
- MEDITATIVE: extended reflection, minimal forward action

Choose the narrowest descriptor that fits the chapter's dominant pacing. Produce exactly one entry per chapter, in chapter order.

Tone (per chapter):
For every chapter in order, assign one or more tone descriptors — single lowercase words that capture the chapter's dominant emotional and atmospheric register. Examples: "grimdark", "melancholic", "tense", "lyrical", "hopeful", "comic", "contemplative", "whimsical", "triumphant", "mournful", "ironic", "warm".

- Use the descriptors that actually fit; do not force-fit from a fixed vocabulary
- Multiple tones allowed per chapter when the chapter is tonally blended
- Only dominant tones — do not list every possible tonal shade
- Order descriptors by dominance (primary tone first)

Produce exactly one list per chapter, in chapter order.

Rhythm (one description for the whole book):
One sentence describing sentence-level rhythm across the book. Capture any consistent pattern or deliberate variation. Examples: "Short declarative sentences in action, long flowing prose in reflection." or "Uniformly layered sentences with heavy subordinate clauses." Present tense.

Signature features (list, whole book):
Distinctive stylistic features that recur across the book. Single short phrases. Include features that are consistently present OR deliberately recurring, not every feature that appeared once. Examples: "heavy dialogue with minimal tags", "sensory density in action scenes", "epistolary fragments between chapters", "in-world documents quoted", "stream of consciousness in flashbacks".

Guidance:
- The pacing list length must equal the tone list length must equal the number of chapters
- Describe, do not judge — "grimdark" is a descriptor, "overly grim" is evaluation
- Draw only from what the style summaries establish
- Synthesize across chapters for rhythm and signature_features; per-chapter for pacing and tone

Your input will be the style summaries of every chapter in the book, concatenated in order with chapter headers."""
