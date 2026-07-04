"""Paired statistics for GI vs Suppress: Wilcoxon signed-rank p-value and a
rank-biserial effect size, over paired (scenario, seed) block-rate observations.
"""

from gi.stats import paired_comparison


def test_strong_separation_is_significant_with_large_effect():
    # GI consistently lower than Suppress across pairs
    gi = [0.1, 0.0, 0.08, 0.17, 0.0, 0.1]
    suppress = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    result = paired_comparison(gi, suppress)
    assert result["n_pairs"] == 6
    assert result["median_gi"] < result["median_suppress"]
    assert result["p_value"] < 0.05
    assert result["effect_size"] >= 0.99  # GI < Suppress in every pair


def test_no_difference_is_not_significant():
    same = [0.3, 0.3, 0.3, 0.3, 0.3]
    result = paired_comparison(same, same)
    assert result["p_value"] >= 0.05
