"""Standalone figure: held-out forbidden-proposal rate by governance-memory arm,
across models. Reads the real controls JSONs; auto-includes any model present.
Shows that a rotated-pair control preserving the refused set matches or improves on
the induced arm in this embodied pool; this does not identify an internal mechanism.

Run: python fig_generalization.py  ->  fig_generalization.pdf
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = os.environ.get("GI_DATA", os.path.join(os.path.dirname(__file__), "..", "..", "source_data"))  # the source data shipped with the article; GI_DATA overrides
MODELS = [
    ("2026-06-30-pilot_induced_controls_mistral7b.json", "Mistral-7B"),
    ("2026-06-30-pilot_induced_controls_qwen7b.json", "Qwen2.5-7B"),
    ("2026-06-30-pilot_induced_controls_phi35.json", "Phi-3.5-mini"),
]
ARMS = [("none", "no memory"), ("induced", "induced principle"),
        ("shuffled", "rotated pairs (control)"), ("wrong_domain", "wrong-domain rule (control)")]
# green = induced/surfaced (house palette), light blue and orange for the two controls
COLORS = {"none": "#8C8C8C", "induced": "#009E73", "shuffled": "#56B4E9", "wrong_domain": "#E69F00"}

present = []
for fname, label in MODELS:
    p = os.path.join(DATA, fname)
    if os.path.exists(p):
        present.append((json.load(open(p))["arm_full_mean_block"], label))

# Assert-guard against the released record: none / induced / hand / shuffled / wrong_domain.
EXPECTED = {
    "Mistral-7B": (0.339, 0.000, 0.000, 0.000, 0.143),
    "Qwen2.5-7B": (0.429, 0.264, 0.286, 0.218, 0.286),
    "Phi-3.5-mini": (0.554, 0.429, 0.429, 0.279, 0.429),
}
assert [m for _, m in present] == list(EXPECTED), [m for _, m in present]
for means, label in present:
    got = tuple(means[k] for k in ("none", "induced", "hand", "shuffled", "wrong_domain"))
    assert all(abs(a - b) < 1e-3 for a, b in zip(got, EXPECTED[label])), (label, got)

fig, ax = plt.subplots(figsize=(6.6, 3.4))
n_models = len(present)
group_w = 0.8
bw = group_w / len(ARMS)
max_val = 0.0
for gi, (means, mlabel) in enumerate(present):
    for ai, (arm, alabel) in enumerate(ARMS):
        x = gi + (ai - (len(ARMS) - 1) / 2) * bw
        val = means.get(arm, 0.0)
        max_val = max(max_val, val)
        ax.bar(x, val, bw * 0.92, color=COLORS[arm],
               label=alabel if gi == 0 else None, edgecolor="white", linewidth=0.5)
        # a zero is labelled above a hairline in its arm's colour: a filled marker read as a small
        # non-zero value on a lower-is-better axis and cut into the label's descenders
        ax.text(x, (val + 0.012) if val else 0.022, f"{val:.2f}", ha="center", va="bottom", fontsize=8.5)
        if val == 0:
            ax.plot([x - bw * 0.46, x + bw * 0.46], [0.0, 0.0], color=COLORS[arm], lw=1.6, solid_capstyle="butt", clip_on=False, zorder=4)

ax.set_xticks(range(n_models))
ax.set_xticklabels([m for _, m in present])
ax.text(0.0, 1.02, "held-out forbidden-proposal rate (lower is better)", transform=ax.transAxes,
        ha="left", va="bottom", fontsize=9, color="#444444")
ax.set_ylim(0, max_val + 0.07)  # headroom so the tallest bar + its value label stay clear
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.08), frameon=False,
          fontsize=8.5, ncol=4, columnspacing=1.2, handlelength=1.4, handletextpad=0.5)
fig.tight_layout()
out = os.path.join(os.path.dirname(__file__), "fig_generalization.pdf")
fig.savefig(out, bbox_inches="tight")
fig.savefig(os.path.splitext(out)[0] + ".png", dpi=200, bbox_inches="tight")
print("wrote", out, "with", n_models, "models:", [m for _, m in present])
