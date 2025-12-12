from typing import List, Dict
from toon import encode


PACING_AND_STRUCTURE_SYSTEM_PROMPT = """You are an expert story analyst specializing in narrative structure, pacing, and dramatic tension.

Your task is to analyze a story's accumulated context and all structure extraction data to generate comprehensive pacing and structural analysis.

# Your Responsibilities

1. **Map tension curves** across the entire story to visualize dramatic arc
2. **Identify pacing patterns** and detect issues (sagging middle, rushed endings, exposition dumps)
3. **Analyze scene composition** and distribution across the story
4. **Track POV usage** and character perspective distribution
5. **Chart emotional journey** intended for the reader
6. **Assess thematic consistency** and symbol usage
7. **Evaluate show vs tell balance** and identify problem chapters
8. **Determine structural framework** and key story beats
9. **Provide actionable recommendations** for improving pacing and structure

# Quality Standards

- **Tension curves** should accurately reflect dramatic progression with chapter-by-chapter data
- **Pacing patterns** should identify distinct sections with different rhythms
- **Issues** must cite specific chapters and provide concrete metrics
- **Recommendations** should be actionable, not vague ("Add tension" → "Introduce obstacle in Ch. 12")
- **Structural assessment** should identify actual patterns, not force fit to templates

# Important Notes

- Focus on **what actually appears in the story**, not theoretical ideals
- Different genres have different pacing expectations (thriller vs literary fiction)
- Pacing "issues" are only issues if they're unintentional or harm the story
- Multiple POVs aren't inherently better/worse than single POV
- Low tension chapters aren't bad if they serve a purpose (recovery, world-building)

# Output Format

Return a complete PacingAndStructureAnalysis with:
- Chapter-by-chapter tension tracking
- Pacing patterns across story sections
- Comprehensive scene and POV statistics
- Emotional and thematic analysis
- Show vs tell assessment
- Structural framework identification
- Specific, actionable recommendations

Be thorough, insightful, and true to the story."""


def build_pacing_and_structure_extraction_prompt(
    story_context: str,
    structure_extractions: List[Dict | None],
    story_title: str,
    total_chapters: int
) -> str:
    """
    Build the user prompt for pacing and structure analysis.
    
    Args:
        story_context: TOON-encoded accumulated story context
        structure_extractions: List of structure extraction dicts from all chapters
        story_title: Title of the story
        total_chapters: Total number of chapters analyzed
        
    Returns:
        Complete user prompt string
    """
    
    # Encode structure extractions as TOON for token efficiency
    structure_extractions_toon = encode({
        "chapters": [
            {
                "chapter_number": i + 1,
                "extraction": extraction
            }
            for i, extraction in enumerate(structure_extractions)
        ]
    })
    
    prompt = f"""# STORY ANALYSIS TASK

Generate comprehensive pacing and structural analysis for: **{story_title}**

Total chapters analyzed: {total_chapters}

{'═' * 80}

# ACCUMULATED STORY CONTEXT (TOON Format)

{story_context}

{'═' * 80}

# STRUCTURE EXTRACTIONS BY CHAPTER (TOON Format)

Below are the structure-focused extractions from each chapter, showing:
- Structural role (setup, rising_action, climax, etc.)
- Scenes (type, POV, goals, conflicts, outcomes)
- Pacing analysis (action/dialogue/introspection/exposition percentages)
- Themes explored
- Emotional beats
- Show vs tell ratio

{structure_extractions_toon}

{'═' * 80}

# YOUR TASK: PACING AND STRUCTURE ANALYSIS

Analyze all the data above and create comprehensive pacing and structural analysis.

## Step 1: Build Tension Curve

Extract tension data from each chapter's pacing analysis:

**For each chapter, create a TensionPoint:**
```json
{{
  "chapter": 5,
  "tension_level": 7,
  "structural_role": "rising_action",
  "key_event": "Vex discovers conspiracy evidence"
}}
```

**Analyze the curve:**
- `average_tension`: Mean across all chapters
- `tension_range`: "Ranges from 2 (low) to 9 (climax)"
- `tension_trend`: "rising" (builds steadily), "falling" (diminishes), "fluctuating" (up and down), "flat" (stays same)

**Good tension curves:**
- Steady rise with peaks and valleys (not flat)
- Higher at climax than at start
- Recovery periods after intense moments

## Step 2: Identify Pacing Patterns

Group chapters into sections with similar pacing characteristics:

**Example PacingPattern:**
```json
{{
  "chapter_range": "Chapters 1-8",
  "dominant_pace": "moderate",
  "action_average": 0.35,
  "dialogue_average": 0.40,
  "introspection_average": 0.15,
  "exposition_average": 0.10,
  "description": "Setup phase with balanced mix of action and character establishment. Steady pacing with clear goals."
}}
```

**Assess overall pace:**
- "fast": High action (40%+), low introspection
- "moderate": Balanced mix
- "slow": High introspection/exposition, low action
- "varied": Intentional shifts between fast and slow

**Pace consistency:**
- "consistent": Maintains rhythm throughout
- "variable": Changes with purpose (builds to climax)
- "erratic": Random shifts that confuse

## Step 3: Analyze Scenes

Aggregate scene data from all chapters:

**Scene Statistics:**
```json
{{
  "total_scenes": 156,
  "average_scenes_per_chapter": 4.9,
  "scene_type_distribution": {{
    "action": 45,
    "dialogue": 62,
    "introspection": 28,
    "exposition": 21
  }},
  "scene_type_percentages": {{
    "action": 0.29,
    "dialogue": 0.40,
    "introspection": 0.18,
    "exposition": 0.13
  }},
  "average_scene_length": 1250,
  "longest_scene": {{
    "chapter": 28,
    "scene": 3,
    "word_count": 5000,
    "type": "action"
  }},
  "shortest_scene": {{
    "chapter": 7,
    "scene": 2,
    "word_count": 300,
    "type": "introspection"
  }}
}}
```

**Identify patterns:**
- Too many short scenes = choppy feeling
- Too many long scenes = slow pacing
- Unbalanced scene types = genre mismatch

## Step 4: Track POV Distribution

**POVAnalysis:**
```json
{{
  "pov_characters": ["Commander Vex", "Dr. Chen", "Admiral Kora"],
  "pov_distribution": {{
    "Commander Vex": 120,
    "Dr. Chen": 25,
    "Admiral Kora": 11
  }},
  "pov_percentages": {{
    "Commander Vex": 0.77,
    "Dr. Chen": 0.16,
    "Admiral Kora": 0.07
  }},
  "dominant_pov": "Commander Vex",
  "pov_switches_per_chapter": 1.8,
  "multi_pov_story": true
}}
```

**Assess POV usage:**
- Single POV: One character throughout
- Multi-POV: Multiple perspectives
- Too many switches per chapter can be disorienting
- Secondary POVs should have purpose, not just variety

## Step 5: Chart Emotional Journey

**EmotionalArc:**
```json
{{
  "emotional_peak_chapters": [3, 15, 18, 28],
  "emotional_valley_chapters": [7, 12],
  "dominant_emotions": ["tension", "hope", "fear", "determination"],
  "emotional_range": "moderate",
  "emotional_progression": "Story moves from fear and uncertainty in opening through determination in middle acts to hope mixed with dread at climax. Ends on cautious optimism.",
  "weak_emotional_beats": [
    {{
      "chapter": 7,
      "issue": "No strong emotional moments - feels like filler"
    }},
    {{
      "chapter": 12,
      "issue": "Emotional beats marked 'weak' in extraction"
    }}
  ]
}}
```

**Emotional range:**
- "narrow": 1-2 emotions (e.g., only tension)
- "moderate": 3-5 emotions
- "wide": 6+ different emotions

## Step 6: Analyze Thematic Patterns

**ThematicAnalysis:**
```json
{{
  "recurring_themes": {{
    "trust": [1, 5, 8, 12, 15, 18, 22, 28],
    "duty_vs_morality": [3, 7, 15, 20, 28],
    "isolation": [1, 8, 15, 22]
  }},
  "theme_frequencies": {{
    "trust": 8,
    "duty_vs_morality": 5,
    "isolation": 4
  }},
  "primary_themes": ["trust", "duty_vs_morality", "isolation"],
  "theme_introduction": {{
    "trust": 1,
    "duty_vs_morality": 3,
    "isolation": 1
  }},
  "theme_resolution": {{
    "trust": 28,
    "duty_vs_morality": 28,
    "isolation": 22
  }},
  "symbols_used": {{
    "broken mirror": [3, 15, 29],
    "artifact": [5, 12, 18, 28]
  }},
  "thematic_consistency": "strong"
}}
```

**Consistency levels:**
- "strong": Themes woven throughout, developed consistently
- "moderate": Themes present but sporadic
- "weak": Themes mentioned but not explored

## Step 7: Evaluate Show vs Tell

**ShowVsTellAnalysis:**
```json
{{
  "overall_ratio": 0.68,
  "ratio_by_chapter": {{
    "1": 0.75,
    "2": 0.70,
    "3": 0.80,
    "8": 0.25,
    ...
  }},
  "problematic_chapters": [
    {{
      "chapter": 8,
      "ratio": 0.25,
      "issue": "Heavy exposition dump explaining backstory"
    }},
    {{
      "chapter": 14,
      "ratio": 0.30,
      "issue": "Telling emotions instead of showing through action"
    }}
  ],
  "exemplary_chapters": [
    {{
      "chapter": 3,
      "ratio": 0.85,
      "strength": "Reveals conspiracy through tense action sequence"
    }},
    {{
      "chapter": 28,
      "ratio": 0.90,
      "strength": "Climax shows character growth through choices"
    }}
  ],
  "trend": "improving"
}}
```

**Ratio interpretation:**
- 0.0-0.3: Too much telling (exposition-heavy)
- 0.4-0.6: Balanced
- 0.7-1.0: Strong showing (immersive)

**Trends:**
- "improving": Ratio increases over story
- "declining": Gets more telly
- "stable": Consistent throughout
- "inconsistent": Wild swings

## Step 8: Assess Story Structure

**Identify structural framework:**

**Three-Act Structure:**
- Act 1 (Setup): ~25% of story
- Act 2 (Confrontation): ~50% of story  
- Act 3 (Resolution): ~25% of story

**Five-Act Structure:**
- Exposition, Rising Action, Climax, Falling Action, Resolution

**Hero's Journey:**
- Ordinary World → Call to Adventure → Refusal → Meeting Mentor → Crossing Threshold → Tests → Approach → Ordeal → Reward → Road Back → Resurrection → Return

**Other patterns:**
- Kishotenketsu (introduction, development, twist, conclusion)
- Episodic (self-contained chapters)
- Non-linear (flashbacks, multiple timelines)

**StructuralAssessment:**
```json
{{
  "story_structure": "three_act",
  "act_breakdown": {{
    "Act 1 (Setup)": "Chapters 1-8",
    "Act 2 (Confrontation)": "Chapters 9-24",
    "Act 3 (Resolution)": "Chapters 25-32"
  }},
  "key_structural_beats": {{
    "inciting_incident": 3,
    "first_plot_point": 8,
    "midpoint": 16,
    "second_plot_point": 24,
    "climax": 28,
    "resolution": 32
  }},
  "structural_balance": "back_heavy",
  "missing_beats": ["clear midpoint reversal"]
}}
```

**Balance assessment:**
- "well_balanced": Acts proportional to structure
- "front_heavy": Too much setup, rushed ending
- "back_heavy": Short setup, long middle/ending
- "uneven": Acts wildly disproportionate

## Step 9: Detect Pacing Issues

**Common pacing problems:**

**Sagging Middle:**
```json
{{
  "issue_type": "sagging_middle",
  "chapters_affected": [12, 13, 14, 15, 16, 17, 18],
  "severity": "major",
  "description": "Tension drops from 6 to 3.5 average. Heavy dialogue (65%) and introspection (25%). Minimal plot progression.",
  "recommendation": "Compress chapters 14-17 into 2-3 chapters. Add subplot complication or deadline pressure in chapter 15 to spike tension.",
  "metrics": {{
    "avg_tension": 3.5,
    "dialogue_pct": 0.65,
    "action_pct": 0.10
  }}
}}
```

**Rushed Ending:**
```json
{{
  "issue_type": "rushed_ending",
  "chapters_affected": [29, 30, 31, 32],
  "severity": "moderate",
  "description": "Climax and resolution compressed into 4 chapters after 28-chapter buildup. Major plot threads resolved in single scenes.",
  "recommendation": "Expand Act 3 by 2-3 chapters to give climax room to breathe. Let resolution span 2 chapters instead of 1.",
  "metrics": {{
    "act_3_percentage": 0.12,
    "expected_percentage": 0.25
  }}
}}
```

**Slow Start:**
```json
{{
  "issue_type": "slow_start",
  "chapters_affected": [1, 2, 3, 4],
  "severity": "moderate",
  "description": "Inciting incident doesn't occur until chapter 5. First 4 chapters are setup with low tension (avg 2.5) and heavy exposition (40%).",
  "recommendation": "Move inciting incident to chapter 2-3. Cut exposition from chapters 1-2 and weave backstory into action.",
  "metrics": {{
    "avg_tension": 2.5,
    "exposition_pct": 0.40
  }}
}}
```

**Monotonous Pace:**
```json
{{
  "issue_type": "monotonous_pace",
  "chapters_affected": [5, 6, 7, 8, 9, 10],
  "severity": "moderate",
  "description": "Six consecutive chapters with identical pacing profile: 30% action, 40% dialogue, 20% introspection, 10% exposition. Tension stays flat at 5.",
  "recommendation": "Vary scene types. Add high-tension spike in chapter 7 or 8. Follow with recovery chapter.",
  "metrics": {{
    "tension_variance": 0.2,
    "pace_sameness": 0.95
  }}
}}
```

**Exposition Dump:**
```json
{{
  "issue_type": "exposition_dump",
  "chapters_affected": [8],
  "severity": "major",
  "description": "Chapter 8 is 60% exposition explaining conspiracy backstory. Show/tell ratio drops to 0.15. Stops narrative momentum.",
  "recommendation": "Break exposition across chapters 6-10 in dialogue or discovery scenes. Show documents, have characters piece together clues.",
  "metrics": {{
    "exposition_pct": 0.60,
    "show_tell_ratio": 0.15
  }}
}}
```

**Uneven Tension:**
```json
{{
  "issue_type": "uneven_tension",
  "chapters_affected": [10, 11, 12, 13],
  "severity": "minor",
  "description": "Tension fluctuates wildly: 8 → 3 → 7 → 2 without clear reason. Creates whiplash effect.",
  "recommendation": "Smooth transitions between high and low tension. Build to peaks more gradually.",
  "metrics": {{
    "tension_variance": 3.2,
    "expected_variance": 1.5
  }}
}}
```

## Step 10: Calculate Scores and Provide Recommendations

**Pacing Score (1-10):**
Consider:
- Tension curve shape (builds to climax?)
- Pace variety (not monotonous?)
- Issue severity (major issues = lower score)
- Genre appropriateness

**Structure Score (1-10):**
Consider:
- Clear framework present?
- Key beats identified?
- Balanced acts?
- Missing structural elements?

**Key Recommendations:**
Provide 3-5 actionable recommendations prioritized by impact:

Good recommendations:
- "Compress chapters 14-17 into 2 chapters to tighten sagging middle"
- "Move inciting incident from Chapter 5 to Chapter 2"
- "Add tension spike in Chapter 15 with deadline or betrayal"
- "Expand climax from 1 chapter to 2-3 chapters for proper resolution"
- "Reduce exposition in Chapter 8 from 60% to 25%; weave into dialogue"

Bad recommendations (too vague):
- "Improve pacing"
- "Add more action"
- "Make it more exciting"

{'═' * 80}

# OUTPUT SCHEMA

Return JSON matching this exact structure:
```json
{{
  "tension_curve": [
    {{
      "chapter": 1,
      "tension_level": 4,
      "structural_role": "setup",
      "key_event": "Introduction of protagonist in ordinary world"
    }}
  ],
  "average_tension": 5.8,
  "tension_range": "Ranges from 2 (low) to 9 (climax)",
  "tension_trend": "rising",
  "pacing_patterns": [
    {{
      "chapter_range": "Chapters 1-8",
      "dominant_pace": "moderate",
      "action_average": 0.35,
      "dialogue_average": 0.40,
      "introspection_average": 0.15,
      "exposition_average": 0.10,
      "description": "Setup phase with balanced pacing..."
    }}
  ],
  "overall_pace": "varied",
  "pace_consistency": "variable",
  "scene_statistics": {{
    "total_scenes": 156,
    "average_scenes_per_chapter": 4.9,
    "scene_type_distribution": {{"action": 45, "dialogue": 62}},
    "scene_type_percentages": {{"action": 0.29, "dialogue": 0.40}},
    "average_scene_length": 1250,
    "longest_scene": {{"chapter": 28, "scene": 3, "word_count": 5000, "type": "action"}},
    "shortest_scene": {{"chapter": 7, "scene": 2, "word_count": 300, "type": "introspection"}}
  }},
  "pov_analysis": {{
    "pov_characters": ["Commander Vex", "Dr. Chen"],
    "pov_distribution": {{"Commander Vex": 120, "Dr. Chen": 36}},
    "pov_percentages": {{"Commander Vex": 0.77, "Dr. Chen": 0.23}},
    "dominant_pov": "Commander Vex",
    "pov_switches_per_chapter": 1.2,
    "multi_pov_story": true
  }},
  "emotional_arc": {{
    "emotional_peak_chapters": [3, 15, 28],
    "emotional_valley_chapters": [7, 18],
    "dominant_emotions": ["tension", "hope", "fear"],
    "emotional_range": "moderate",
    "emotional_progression": "Fear → determination → hope...",
    "weak_emotional_beats": [
      {{"chapter": 7, "issue": "No strong emotional moments"}}
    ]
  }},
  "thematic_analysis": {{
    "recurring_themes": {{"trust": [1, 5, 8, 12]}},
    "theme_frequencies": {{"trust": 4}},
    "primary_themes": ["trust", "duty"],
    "theme_introduction": {{"trust": 1}},
    "theme_resolution": {{"trust": 28}},
    "symbols_used": {{"broken mirror": [3, 15]}},
    "thematic_consistency": "strong"
  }},
  "show_vs_tell": {{
    "overall_ratio": 0.68,
    "ratio_by_chapter": {{"1": 0.75, "2": 0.70}},
    "problematic_chapters": [
      {{"chapter": 8, "ratio": 0.25, "issue": "Heavy exposition"}}
    ],
    "exemplary_chapters": [
      {{"chapter": 3, "ratio": 0.85, "strength": "Immersive action"}}
    ],
    "trend": "improving"
  }},
  "structural_assessment": {{
    "story_structure": "three_act",
    "act_breakdown": {{
      "Act 1 (Setup)": "Chapters 1-8",
      "Act 2 (Confrontation)": "Chapters 9-24",
      "Act 3 (Resolution)": "Chapters 25-32"
    }},
    "key_structural_beats": {{
      "inciting_incident": 3,
      "midpoint": 16,
      "climax": 28
    }},
    "structural_balance": "well_balanced",
    "missing_beats": []
  }},
  "pacing_issues": [
    {{
      "issue_type": "sagging_middle",
      "chapters_affected": [12, 13, 14],
      "severity": "moderate",
      "description": "Tension drops, heavy dialogue...",
      "recommendation": "Compress or add complication...",
      "metrics": {{"avg_tension": 3.5}}
    }}
  ],
  "total_chapters": 32,
  "total_estimated_words": 85000,
  "average_chapter_length": 2656,
  "pacing_score": 7,
  "structure_score": 8,
  "pacing_summary": "Story maintains varied pace with clear tension escalation...",
  "structural_summary": "Follows three-act structure with well-defined beats...",
  "key_recommendations": [
    "Compress chapters 14-17 to tighten sagging middle",
    "Add tension spike in chapter 15",
    "Reduce exposition in chapter 8 from 60% to 25%"
  ]
}}
```

{'═' * 80}

# CRITICAL REQUIREMENTS

1. **Tension curve must include all chapters** with specific tension levels
2. **Pacing patterns should group logically** (not one per chapter)
3. **Scene statistics must be accurate** (counts, averages, percentages sum to 1.0)
4. **POV percentages must sum to 1.0**
5. **Issue severity must match description** (don't call minor issues major)
6. **Recommendations must be specific** with chapter numbers and actions
7. **Scores must be justified** by the analysis (don't inflate)
8. **Chapter references must be integers**
9. **All metrics in issues must be relevant** (don't include random data)
10. **Structural balance must match act breakdown** (if Act 2 is 60%, it's "back_heavy" not "well_balanced")

{'═' * 80}

# QUALITY CHECKLIST

✓ Tension curve includes all chapters  
✓ Tension trend matches curve data  
✓ Pacing patterns cover entire story  
✓ Scene type percentages sum to 1.0  
✓ POV percentages sum to 1.0  
✓ Emotional peaks/valleys justified by data  
✓ Themes tracked across multiple chapters  
✓ Show/tell ratios match chapter data  
✓ Structural beats align with chapter roles  
✓ Issues cite specific chapters and metrics  
✓ Recommendations are actionable  
✓ Scores match severity of issues  
✓ Summaries are 2-3 sentences  

{'═' * 80}

Begin pacing and structure analysis now. Return ONLY the JSON object matching the PacingAndStructureAnalysis schema. No preamble, no markdown code blocks, just the JSON.
"""
    
    return prompt