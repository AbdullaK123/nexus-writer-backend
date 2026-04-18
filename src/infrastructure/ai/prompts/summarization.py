



_SHARED_IMPORTANCE_RULE = """
Include only facts that matter for understanding later chapters, character arcs, the world's canon, or the book as a whole. Apply this test to every candidate fact: "If a reader skipped this chapter, would missing this fact hurt their understanding of what comes after?" If no, omit it.

Specifically skip:
- Incidental actions (pouring tea, lighting a cigarette, crossing a room) unless they carry weight
- Routine dialogue that doesn't advance plot, reveal character, or establish world
- Physical descriptions that don't matter for later events
- Background atmosphere, weather, sensory detail that is pure texture
- Anything a reader would forget by the next chapter without consequence

Include:
- First-time introductions of people, places, factions, technologies
- Actions with downstream consequences
- Revelations, decisions, commitments, betrayals, deaths
- Statements that establish fact about the world or characters
- Shifts in relationships or power dynamics

When in doubt, leave it out. A summary that misses a minor beat is recoverable. A summary drowning in trivia is useless.
""".strip()


PLOT_SUMMARY_PROMPT = f"""You are summarizing a chapter of a novel for use as narrative context in downstream AI tasks. Your job is to extract the important plot facts — what happened that matters for the rest of the book.

Scope: events, actions, state changes, causal chains with forward relevance.

{_SHARED_IMPORTANCE_RULE}

Include (when important):
- Who did what, where, when
- Plot-driving dialogue (paraphrased, not quoted)
- Significant state changes: location shifts that matter, possessions gained or lost, knowledge acquired, alliances formed or broken, injuries, deaths
- Discoveries and revelations
- Decisions made and their stated reasons

Exclude:
- Routine movement and action without plot weight
- Thematic interpretation or literary commentary
- Emotional framing ("heartbreakingly", "tensely")
- Foreshadowing speculation
- Prose style observations
- Internal states (those belong in character summary)
- Minor beats that won't echo forward

Output format:
- Bulleted list, one fact per bullet
- Past tense
- Named entities verbatim
- Each bullet a complete, standalone fact
- Chronological order within the chapter
- Start bullets with a noun phrase or name, not a pronoun

Length: Minimum bullets that capture what matters. A quiet chapter may need 2-4 bullets. A pivotal chapter may need 10-15. Do not pad."""


CHARACTER_SUMMARY_PROMPT = f"""You are summarizing a chapter of a novel for use as character-tracking context in downstream AI tasks. Your job is to extract the important character facts — what was established about the people in this chapter that matters for their arcs.

Scope: significant character appearances, actions, stated internal states, relationships, revealed backstory.

{_SHARED_IMPORTANCE_RULE}

Epistemic rule for internal states:
POV and distance varies across chapters. Preserve internal states when narration states them directly ("She was afraid", "He distrusted the stranger", a character's direct thought). Do NOT infer internal states from behavior alone. "Clenched fists" does not justify "he was angry" unless anger is also narrated.

Include (when important):
- Named characters who appeared and did something that matters
- Actions with consequence for their arc
- Internal states the narration states directly
- Statements about relationships ("they had been lovers", "she trusted him")
- Backstory revealed in this chapter
- Physical or situational changes significant to the character's arc (injury, new possession that matters, aging)
- First appearances of new named characters (always important by definition)

Exclude:
- Incidental presence without meaningful action
- Inferred psychology not stated in text
- Thematic readings of character arcs
- Your interpretation of what a character "represents"
- Plot events that don't reveal character (those go in plot summary)
- World-building details (those go in world summary)
- Minor interactions that won't matter later

Output format:
- Group by character. One subsection per named character who did something important.
- Bulleted facts within each character's section.
- Past tense.
- Character names verbatim.
- New characters marked: "[NEW] Character Name"

Example:
Morinth:
- Revealed she had been tracking the Phoenix signal for six months
- Stated distrust of Saedaris's motives
- Agreed to travel to the outer system despite her suspicions

[NEW] Saedaris:
- Introduced as a Turian ex-military pilot
- Needed parts for a damaged warp core
- Withheld his reason for pursuing the Phoenix signal

Omit characters who appeared but did nothing significant. If a character had a walk-on role with no bearing on their arc, leave them out.

Length: Scale to significance, not to headcount."""


WORLD_SUMMARY_PROMPT = f"""You are summarizing a chapter of a novel for use as worldbuilding context in downstream AI tasks. Your job is to extract the important world facts — what was established as canon that matters for understanding the universe.

Scope: significant facts about places, factions, technologies, biologies, cultures, histories, rules.

{_SHARED_IMPORTANCE_RULE}

A world fact is "important" if it:
- Introduces something new to the canon (always include)
- Clarifies or extends something previously established
- Establishes a rule or constraint that could matter later
- Reveals history, politics, or culture with forward weight

A world fact is NOT important if it:
- Is sensory texture (the wind, the temperature, the smell of the spaceport)
- Repeats what's already been established without adding
- Describes a place or thing the characters are passing through without consequence

Include (when important):
- Places newly introduced or newly described in meaningful detail
- Factions, organizations, governments with canonical facts
- Technologies, magic, biologies — especially their rules and limits
- Cultural facts with weight (customs that will matter, languages, social structures)
- Historical events referenced
- Physical laws or anomalies specific to this world

Exclude:
- Plot events (those go in plot summary)
- Character interiority (those go in character summary)
- Atmospheric description without canon weight
- Interpretations of themes
- Speculation about how things "probably" work if not stated

Output format:
- Grouped by category: Places, Factions, Technology, Culture, History, Other.
- Omit empty categories.
- Bulleted facts.
- Past tense, except for stated world-rules which can be present.
- Entity names verbatim.
- New entities: "[NEW] Entity Name"

Example:
Places:
- [NEW] Tarsus-IV: a remote spaceport in the outer Serpentis system, described as a hub for salvagers

Technology:
- Warp cores required regular calibration with rare-earth elements
- [NEW] The Phoenix signal operated on a frequency previously unknown to Citadel science

If no new or clarifying world facts appeared, output: "No new world-building in this chapter."

Length: Scale to density of canonical content. Many chapters will have little. Do not invent to fill."""


STYLE_SUMMARY_PROMPT = """You are describing the stylistic register of a chapter of a novel for use as voice-matching context in downstream AI tasks. Your job is to describe how this chapter reads, not what happens in it.

Scope: POV, tense, tone, pacing, notable stylistic choices.

This summary captures voice, not content. Every chapter has a style worth noting even if nothing plot-important happened.

Include:
- Point of view (first person / close third / omniscient / second person)
- POV character, if applicable
- Tense (past / present)
- Tone register (grimdark, lyrical, clinical, comic, elegiac, terse, ornate, etc.)
- Pacing (scene-level action, extended reflection, rapid cuts, long setpiece)
- Sentence rhythm (short and punchy, long and flowing, mixed)
- Notable features (heavy dialogue, stream of consciousness, epistolary fragments, sensory density, restraint in description)
- Shifts within the chapter (POV change, tense shift, register change)

Exclude:
- Plot or character content
- Evaluation ("beautifully written") — describe, don't judge
- Interpretation of the author's stylistic motives

Output format:
- Bulleted facts, present tense (describing the prose itself).
- Short. 3-6 bullets typical.

Example:
- Close-third POV, Morinth
- Past tense throughout
- Grimdark register with restrained sensory detail
- Rhythm alternates between short declarative sentences and extended internal monologue
- Heavy dialogue in the second half; dialogue tags minimal
- Single continuous scene, no breaks"""