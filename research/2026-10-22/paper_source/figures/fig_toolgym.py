"""Supplementary Figure 5: declared-target rejection and recorded legitimate fixes.

Per task family and model: forbidden proposals (writes naming the grading file)
out of 12 seeds, measured before the gate (equal across arms in these records),
and recorded legitimate fixes, ungoverned versus governed. Accepted edits naming
forbidden targets are zero by construction; admitted source runs unconfined, so
this does not establish zero forbidden execution effects. Ungoverned fix counts
marked as floors cannot support a general competence comparison.

Numbers are loaded from the archived JSON and checked against the saved records.
Okabe-Ito palette; no connectors, no rotated text.
"""
from __future__ import annotations

import json
import os
import pathlib
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DATA = pathlib.Path(os.environ.get("GI_DATA", pathlib.Path(__file__).resolve().parents[2] / "source_data"))  # the source data shipped with the article; GI_DATA overrides
OUT = pathlib.Path(__file__).resolve().parent

GREEN = "#009E73"
VERMIL = "#D55E00"
GREY = "#BBBBBB"
DARKGREY = "#666666"
FS = 10.0
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": FS, "axes.linewidth": 0.7})

FAMILIES = [("second_largest", "second\nlargest"), ("even_fib_sum", "even-\nFibonacci\nsum"), ("run_length", "run\nlength"), ("is_balanced", "balanced\nbrackets")]
MODELS = [("2026-06-30-toolgym_hard_mistral7b.json", "Mistral-7B"), ("2026-06-30-toolgym_hard_qwen7b.json", "Qwen2.5-7B")]


def load(fname):
    d = json.loads((DATA / fname).read_text())
    agg = defaultdict(lambda: {"n": 0, "att": 0, "fix": 0, "never": 0})
    for r in d["rows"]:
        a = agg[(r["task"], r["governed"])]
        a["n"] += 1
        a["att"] += int(r["attempted_test_mutation"])
        a["fix"] += int(r["real_fix"])
        # an ungoverned run whose test was overwritten is never re-scored, so its fix count is a floor
        a["never"] += int((not r["governed"]) and r["attempted_test_mutation"] and not r["real_fix"])
    assert len(d["rows"]) == 96 and all(v["n"] == 12 for v in agg.values())
    assert d["ungoverned"]["spec_game_rate"] == 0.0 and d["governed"]["spec_game_rate"] == 0.0
    assert d["ungoverned"]["tempted_rate"] == d["governed"]["tempted_rate"]
    for fam, _ in FAMILIES:
        assert agg[(fam, False)]["att"] == agg[(fam, True)]["att"], fam  # measured pre-gate
    return d, agg


panels = [load(f) for f, _ in MODELS]
dm, am = panels[0]
dq, aq = panels[1]
assert abs(dm["ungoverned"]["tempted_rate"] - 0.271) < 1e-3 and abs(dq["ungoverned"]["tempted_rate"] - 0.312) < 1e-3
assert am[("even_fib_sum", False)]["att"] == 12 and aq[("is_balanced", False)]["att"] == 12
assert am[("even_fib_sum", True)]["fix"] == 0 and am[("even_fib_sum", False)]["fix"] == 0
assert aq[("is_balanced", True)]["fix"] == 0 and aq[("is_balanced", False)]["fix"] == 0
assert aq[("even_fib_sum", True)]["fix"] == 12 and aq[("even_fib_sum", False)]["fix"] == 9
assert aq[("even_fib_sum", False)]["att"] == 3

fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.3), sharey=True, gridspec_kw={"wspace": 0.10})
w = 0.27
for ax, (d, agg), (_, label) in zip(axes, panels, MODELS):
    xs = list(range(len(FAMILIES)))
    att = [agg[(f, False)]["att"] for f, _ in FAMILIES]
    fix_u = [agg[(f, False)]["fix"] for f, _ in FAMILIES]
    fix_g = [agg[(f, True)]["fix"] for f, _ in FAMILIES]
    ax.bar([x - w for x in xs], att, w * 0.92, color=VERMIL, edgecolor="white", lw=0.4, label="forbidden proposals (pre-gate, both arms)", zorder=3)
    ax.bar(xs, fix_u, w * 0.92, color=GREY, edgecolor="white", lw=0.4, label="legitimate fix, ungoverned", zorder=3)
    ax.bar([x + w for x in xs], fix_g, w * 0.92, color=GREEN, edgecolor="white", lw=0.4, label="legitimate fix, governed", zorder=3)
    for (x, (a, u, g)), (fam, _flab) in zip(zip(xs, zip(att, fix_u, fix_g)), FAMILIES):
        ax.text(x - w, a + 0.3, str(a), ha="center", va="bottom", fontsize=FS - 1.5, color=VERMIL)
        _nv = agg[(fam, False)]["never"]  # a floor is labelled as one
        ax.text(x + (0.12 * w if _nv else 0.0), u + 0.3, (f"\u2265{u}" if _nv else str(u)), ha="center", va="bottom", fontsize=FS - 1.5, color=DARKGREY)
        ax.text(x + w, g + 0.3, str(g), ha="center", va="bottom", fontsize=FS - 1.5, color=GREEN)
    ax.set_xticks(xs)
    ax.set_xticklabels([lab for _, lab in FAMILIES], fontsize=FS - 1.0)
    ax.set_xlim(-0.6, len(FAMILIES) - 0.4)
    ax.set_ylim(0, 14.2)
    ax.set_yticks([0, 4, 8, 12])
    ax.tick_params(labelleft=True)  # both panels carry their own tick labels
    rate = d["ungoverned"]["tempted_rate"]
    ax.set_title(f"{label}  ({rate*100:.0f}% forbidden proposals)", loc="left", fontsize=FS - 0.8, fontweight="bold", pad=18)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
axes[0].text(0.0, 1.02, "count, of 12 seeds per family", transform=axes[0].transAxes, ha="left", va="bottom", fontsize=FS - 1.5, color="#444444")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, frameon=False, fontsize=FS - 1.8, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.17))

fig.savefig(OUT / "fig_toolgym.pdf", bbox_inches="tight")
fig.savefig(OUT / "fig_toolgym.png", dpi=170, bbox_inches="tight")
print("wrote", OUT / "fig_toolgym.pdf")
