from typing import Any, Dict
from langchain.tools import tool
import textstat
import re


# tool for readability metrics
@tool(description="Calculate various readability metrics for the given text.")
def calculate_readability_metrics(text: str) -> Dict[str, Any]:
    """Calculate various readability metrics for the given text."""
    
    # Calculate all metrics using textstat
    word_count = textstat.lexicon_count(text, removepunct=True)
    sentence_count = textstat.sentence_count(text)
    
    flesch_reading_ease = textstat.flesch_reading_ease(text)
    smog_index = textstat.smog_index(text)
    coleman_liau_index = textstat.coleman_liau_index(text)
    automated_readability_index = textstat.automated_readability_index(text)
    linsear_write_formula = textstat.linsear_write_formula(text)
    gunning_fog_index = textstat.gunning_fog(text)
    dale_chall_readability_score = textstat.dale_chall_readability_score(text)
    text_standard = textstat.text_standard(text, float_output=False)

    metrics: Dict[str, Any] = {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "flesch_reading_ease": flesch_reading_ease,
        "smog_index": smog_index,
        "coleman_liau_index": coleman_liau_index,
        "automated_readability_index": automated_readability_index,
        "linsear_write_formula": linsear_write_formula,
        "gunning_fog_index": gunning_fog_index,
        "dale_chall_readability_score": dale_chall_readability_score,
        "text_standard": text_standard,
    }
    return metrics

@tool(description="Compare two values and return a human-readable string.")
def compare_values(a: float, b: float) -> str:
    """Compare two values and return a human-readable string."""
    if a > b:
        return "The first value is higher."
    elif a < b:
        return "The second value is higher."
    else:
        return (
            "The two values are equal. "
            "This can happen if the text is very short or if the language is English."
        )

@tool(description="Compare two readability metric snapshots and summarize improvements or regressions in readability.")
def compare_readability_metrics(before_metrics: Any, after_metrics: Any) -> str:
    """Compare two readability metrics and return a human-readable string.

    Assumes "better" means easier to read:
    - Higher is better: Flesch Reading Ease
    - Lower is better: SMOG, Coleman-Liau, ARI, Linsear Write, Gunning Fog, Dale-Chall
    Word and sentence counts are reported but not judged as better/worse.
    """
    tol = 1e-3  # tolerance to treat very small differences as unchanged

    def fmt(x: float) -> str:
        return f"{x:.2f}"

    comparisons = [
        ("flesch_reading_ease", "Flesch Reading Ease", True),
        ("smog_index", "SMOG Index", False),
        ("coleman_liau_index", "Coleman-Liau Index", False),
        ("automated_readability_index", "Automated Readability Index (ARI)", False),
        ("linsear_write_formula", "Linsear Write Formula", False),
        ("gunning_fog_index", "Gunning Fog Index", False),
        ("dale_chall_readability_score", "Dale-Chall Readability Score", False),
    ]

    improved = 0
    regressed = 0
    unchanged = 0
    detail_lines = []

    def get_val(obj: Any, key: str) -> Any:
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key)

    for attr, label, higher_is_better in comparisons:
        before = get_val(before_metrics, attr)
        after = get_val(after_metrics, attr)
        delta = float(after) - float(before)
        status = "Unchanged"
        if abs(delta) <= tol:
            unchanged += 1
        else:
            if higher_is_better:
                if delta > 0:
                    improved += 1
                    status = "Improved"
                else:
                    regressed += 1
                    status = "Regressed"
            else:
                if delta < 0:
                    improved += 1
                    status = "Improved (lower is better)"
                else:
                    regressed += 1
                    status = "Regressed (lower is better)"
        sign = "+" if delta >= 0 else ""
        detail_lines.append(
            f"- {label}: {fmt(float(before))} -> {fmt(float(after))} ({sign}{fmt(delta)}) [{status}]"
        )

    # Text standard comparison
    ts_before = get_val(before_metrics, 'text_standard')
    ts_after = get_val(after_metrics, 'text_standard')
    ts_line = f"Text standard: {ts_before} -> {ts_after}"

    # Counts (reported only)
    wc_before, wc_after = get_val(before_metrics, 'word_count'), get_val(after_metrics, 'word_count')
    sc_before, sc_after = get_val(before_metrics, 'sentence_count'), get_val(after_metrics, 'sentence_count')
    counts_lines = [
        f"- Word count: {wc_before} -> {wc_after} ({'+' if wc_after - wc_before >= 0 else ''}{wc_after - wc_before})",
        f"- Sentence count: {sc_before} -> {sc_after} ({'+' if sc_after - sc_before >= 0 else ''}{sc_after - sc_before})",
    ]

    # Overall summary classification
    if improved > regressed and improved > 0:
        overall = "Overall readability improved."
    elif regressed > improved and regressed > 0:
        overall = "Overall readability regressed."
    elif improved == 0 and regressed == 0:
        overall = "No significant change in readability."
    else:
        overall = "Mixed changes in readability."

    header = (
        f"Readability comparison:\n"
        f"{overall} (Improved: {improved}, Regressed: {regressed}, Unchanged: {unchanged})\n"
        f"{ts_line}\n"
        f"Details:\n"
    )

    return "\n".join([header, *detail_lines, "Counts:", *counts_lines])
