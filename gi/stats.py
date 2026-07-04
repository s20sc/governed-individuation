"""Paired statistics for the GI vs Suppress comparison.

Each pair is one (scenario, seed): the GI block rate and the Suppress block rate
under identical task, model, and red-lines. We report a Wilcoxon signed-rank
p-value and a matched-pairs rank-biserial effect size (directional: +1 means GI
undercut Suppress in every pair).
"""

import statistics
from collections.abc import Sequence

from scipy.stats import wilcoxon


def paired_comparison(gi: Sequence[float], suppress: Sequence[float]) -> dict:
    n = len(gi)
    diffs = [g - s for g, s in zip(gi, suppress)]
    n_lower = sum(1 for d in diffs if d < 0)
    n_higher = sum(1 for d in diffs if d > 0)
    effect = (n_lower - n_higher) / n if n else 0.0

    if all(d == 0 for d in diffs):
        p_value = 1.0
    else:
        try:
            p_value = float(wilcoxon(gi, suppress).pvalue)
        except ValueError:
            p_value = 1.0

    return {
        "n_pairs": n,
        "median_gi": statistics.median(gi) if gi else 0.0,
        "median_suppress": statistics.median(suppress) if suppress else 0.0,
        "p_value": p_value,
        "effect_size": effect,
    }
