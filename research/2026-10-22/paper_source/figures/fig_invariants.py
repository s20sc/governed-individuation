"""Supplementary Figure 4 -- the blocked-proposal rate falls only when refusals are surfaced.

(a) Mean blocked-proposal rate per episode window on triggering scenario-by-seed
    pairs, refusals surfaced (governed individuation) for two model families, with
    the suppressed arm drawn at its median over the same pairs (1.0 for both).
(b) Median blocked-proposal rate per model on the triggering pairs, suppressed
    against surfaced, with the paired Wilcoxon p and the sign-dominance effect.

All numbers are loaded from the released JSON and assert-guarded against the
released records. Okabe-Ito palette; no connectors, no rotated text.
"""
from __future__ import annotations

import json
import math
import os
import pathlib
import statistics as st

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DATA = pathlib.Path(os.environ.get("GI_DATA", pathlib.Path(__file__).resolve().parents[2] / "source_data"))  # the source data shipped with the article; GI_DATA overrides
OUT = pathlib.Path(__file__).resolve().parent

GREEN = "#009E73"
VERMIL = "#D55E00"
FS = 10.5  # printed at ~0.86x -> ~9 pt
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": FS, "axes.linewidth": 0.7})

MODELS = [
    ("2026-06-26-study_result_qwen7b.json", "Qwen2.5-7B"),
    ("2026-06-26-study_result_mistral7b.json", "Mistral-7B"),
]

# ---------------- load + assert ----------------
studies = []
for fname, label in MODELS:
    d = json.loads((DATA / fname).read_text())
    inv = d["invariants"]
    assert inv["n_runs"] == 140 and inv["identity_constant_all"] is True, inv
    assert inv["total_permission_violations"] == 0, inv
    trig = [r for r in d["rows"] if r["sup_block"] > 0]
    assert len(trig) == d["stats_triggering"]["n_pairs"]
    assert all(r["gi_viol"] == 0 and r["sup_viol"] == 0 for r in d["rows"])
    W = len(trig[0]["gi_windowed"])
    assert W == 4, W
    curve = [st.mean(r["gi_windowed"][w] for r in trig) for w in range(W)]
    studies.append({"label": label, "trig": trig, "curve": curve, "stats": d["stats_triggering"]})

assert abs(studies[0]["curve"][0] - 0.60) < 1e-9 and studies[0]["curve"][1:] == [0.0, 0.0, 0.0]
assert studies[0]["stats"]["median_gi"] == 0.125 and studies[0]["stats"]["median_suppress"] == 1.0
assert studies[0]["stats"]["p_value"] < 4e-6 and studies[0]["stats"]["effect_size"] == 1.0
assert studies[1]["stats"]["median_gi"] == 0.125 and studies[1]["stats"]["median_suppress"] == 1.0
assert studies[1]["stats"]["p_value"] < 2e-6 and abs(studies[1]["stats"]["effect_size"] - 0.967) < 1e-3
assert (studies[0]["stats"]["n_pairs"], studies[1]["stats"]["n_pairs"]) == (25, 30)


def sci(p: float) -> str:
    e = math.floor(math.log10(p))
    m = p / 10 ** e
    return rf"$p = {m:.1f}\times10^{{{e}}}$"


# ---------------- draw ----------------
fig, (axA, axB) = plt.subplots(1, 2, figsize=(7.4, 3.1), gridspec_kw={"width_ratios": [1.25, 1.0], "wspace": 0.38})


def header(ax, title, metric):
    ax.set_title(title, loc="left", fontsize=FS, fontweight="bold", pad=20)
    ax.text(0.0, 1.02, metric, transform=ax.transAxes, ha="left", va="bottom", fontsize=FS - 1.5, color="#444444")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


# (a) windowed blocked-proposal rate, surfaced per model; suppressed as one median line
x = [1, 2, 3, 4]
styles = [("-", "o"), ("--", "s")]
for s, (ls, mk) in zip(studies, styles):
    axA.plot(x, s["curve"], color=GREEN, ls=ls, marker=mk, ms=5, lw=1.6, label=f"surfaced, {s['label']}", zorder=3)
sup_meds = {s["stats"]["median_suppress"] for s in studies}
assert sup_meds == {1.0}
axA.plot(x, [1.0] * 4, color=VERMIL, ls="-", marker="D", ms=5, lw=1.6, label="suppressed, both models (median)", zorder=3)
axA.set_xticks(x)
axA.set_xlabel("episode window")
axA.set_ylim(-0.04, 1.08)
axA.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
axA.legend(frameon=False, fontsize=FS - 2.2, loc="center right", bbox_to_anchor=(1.0, 0.74), handlelength=2.2, title="refusals", title_fontsize=FS - 2.0)
header(axA, "a  learning only when surfaced", "blocked-proposal rate, triggering pairs")

# (b) median blocked rate per model, suppressed vs surfaced
w = 0.40  # each value label fits inside its own bar slot
for i, s in enumerate(studies):
    axB.bar(i - w / 2, s["stats"]["median_suppress"], w, color=VERMIL, edgecolor="white", lw=0.4, label="suppressed" if i == 0 else None, zorder=3)
    axB.bar(i + w / 2, s["stats"]["median_gi"], w, color=GREEN, edgecolor="white", lw=0.4, label="surfaced" if i == 0 else None, zorder=3)
    axB.text(i - w / 2, s["stats"]["median_suppress"] + 0.02, f"{s['stats']['median_suppress']:.2f}", ha="center", va="bottom", fontsize=FS - 1.5, color=VERMIL)
    axB.text(i + w / 2, s["stats"]["median_gi"] + 0.02, f"{s['stats']['median_gi']:.3f}", ha="center", va="bottom", fontsize=FS - 1.5, color=GREEN)
    axB.text(i, 1.15, sci(s["stats"]["p_value"]) + f"\neffect {s['stats']['effect_size']:.3f}\n{s['stats']['n_pairs'] // 5} scenarios\n5 seeds each",
             ha="center", va="bottom", fontsize=FS - 2.0, color="#333333")
axB.set_xlim(-0.55, 1.55)
axB.set_xticks([0, 1])
axB.set_xticklabels([s["label"] for s in studies])
axB.set_ylim(0, 1.64)  # headroom above the statistics block, clear of the panel subtitle
axB.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
header(axB, "b  medians, triggering pairs", "paired Wilcoxon, sign-dominance effect")

fig.savefig(OUT / "fig_invariants.pdf", bbox_inches="tight")
fig.savefig(OUT / "fig_invariants.png", dpi=170, bbox_inches="tight")
print("wrote", OUT / "fig_invariants.pdf")
