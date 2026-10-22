#!/usr/bin/env python3
"""Supplementary Figure 6 -- what effect mediation can guarantee, and what learned governance and
behavioural testing cannot (three measured limits).

  a. Adversarial false-allow rate falls monotonically with monitor depth,
     name 0.75 -> substring 0.50 -> static path 0.25 -> dynamic 0.00, identically
     across four effect classes (32 encoded attacks; the bars are the
     declared-path evaluation, data/2026-07-02-verifier_eval.json; a separate
     annotation reports data/2026-08-23-live_suite.json).
  b. Mistral endpoint tradeoff: lower violation accompanies more permitted-action
     failures, including possible parse failures; no internal mechanism is identified.
  c. The coverage bound: two frontier models are indistinguishable on a governance
     battery (fingerprint distance 0 within-model, across providers, under a config
     shift), so behavioural attestation carries no substitution signal at ceiling.

Every number is loaded from the released JSON and assert-guarded. Okabe-Ito palette;
no connectors, no rotated text. Standalone PDF per vault rule 7.12.
"""

import json
import os
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402

DATA = pathlib.Path(os.environ.get("GI_DATA", pathlib.Path(__file__).resolve().parents[2] / "source_data"))  # the source data shipped with the article; GI_DATA overrides
OUT = pathlib.Path(__file__).resolve().parent

ORANGE = "#E69F00"
GREEN = "#009E73"
VERMIL = "#D55E00"
GREY = "#8C8C8C"
PURPLE = "#7D6BA6"
FS = 14.5  # printed at 460.935 pt / saved width (~0.50x): FS -> ~7.3 pt, FS-1 -> ~6.8 pt; the smallest text must print at 6.5 pt or more

# ---------------- load + assert ----------------
ver = json.loads((DATA / "2026-07-02-verifier_eval.json").read_text())
assert ver["n_attempts"] == 32, ver["n_attempts"]
fa = ver["false_allow_rate"]
assert (fa["name"], fa["substring"], fa["realpath_static"], fa["realpath_dynamic"]) == (0.75, 0.5, 0.25, 0.0)
pc = ver["per_class_false_allow"]
CLASSES = ["log_tamper", "secret_read", "policy_mutation", "grading_write"]
MONS = ["name", "substring", "realpath_static", "realpath_dynamic"]
for c in CLASSES:  # every class shows the identical monotone ladder
    assert [pc[c][m] for m in MONS] == [0.75, 0.5, 0.25, 0.0], (c, pc[c])
live = json.loads((DATA / "2026-08-23-live_suite.json").read_text())
assert live["n_attempts"] == 96 and live["n_core"] == 32 and live["n_refused_before_commit"] == 96
assert live["false_allow_rate_live_core"] == 0.0 and live["false_allow_rate_live_all"] == 0.0
assert live["n_forbidden_state_unchanged"] == 96 and live["controls_allowed"] == live["n_controls"] == 14

spec = json.loads((DATA / "2026-07-02-pilot_specificity_mistral7b.json").read_text())
arms = {a["arm"]: a for a in spec["arms"]}
assert abs(arms["none"]["violation_rate"] - 0.857) < 1e-3
assert abs(arms["induced"]["violation_rate"] - 0.114) < 1e-3
assert abs(arms["induced"]["over_block_rate"] - 0.257) < 1e-3
assert abs(arms["generic"]["over_block_rate"] - 0.0) < 1e-3
assert abs(arms["generic"]["violation_rate"] - 0.286) < 1e-3
assert abs(arms["none"]["over_block_rate"] - 0.114) < 1e-3

att = json.loads((DATA / "2026-07-02-attestation-summary.json").read_text())["results"]
assert att["cross_model_distance"] == 0.0
assert att["within_model_max_distance"]["frontier_1"] == 0.0 and att["within_model_max_distance"]["frontier_2"] == 0.0
assert att["config_shift_max_distance"]["frontier_1"] == 0.0 and att["config_shift_max_distance"]["frontier_2"] == 0.0
assert att["fraction_choice_A"]["frontier_1"] == 1.0 and att["fraction_choice_A"]["frontier_2"] == 1.0

# ---------------- figure ----------------
fig = plt.figure(figsize=(12.6, 4.0))  # the canvas carries panel c's left-aligned header without a tight-bbox overhang
gs = GridSpec(1, 3, width_ratios=[1.46, 0.98, 0.82], wspace=0.40, left=0.055, right=0.985, bottom=0.17, top=0.78)  # a carries the ladder and its four two-line labels; c is three points at zero, and needs the width to keep its two-line category labels apart


def header(ax, title, metric):
    ax.set_title(title, fontsize=FS, fontweight="bold", loc="left", pad=26)
    ax.text(0.0, 1.03, metric, transform=ax.transAxes, ha="left", va="bottom", fontsize=FS - 1.0, color="#444444")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=FS)


# ---- Panel a: verifier ladder; four sub-bars per monitor are the four effect classes ----
axA = fig.add_subplot(gs[0])
mon_labels = ["name", "substring", "static\npath", "opened\npath"]
mon_colors = [VERMIL, ORANGE, "#B8A000", GREEN]
x = np.arange(len(MONS))
w = 0.19
for j, c in enumerate(CLASSES):
    vals = [pc[c][m] * 100 for m in MONS]
    axA.bar(x + (j - 1.5) * w, vals, w, color=mon_colors, edgecolor="white", linewidth=0.4, alpha=0.62 + 0.13 * (j % 2))
means = [fa[m] * 100 for m in MONS]
for xi, m in zip(x, MONS):
    axA.text(xi, fa[m] * 100 + 3.2, f"{int(fa[m]*100)}%", ha="center", va="bottom", fontsize=FS, fontweight="bold",
             color=mon_colors[list(MONS).index(m)])
axA.set_xticks(x)
axA.set_xticklabels(mon_labels, fontsize=FS)
axA.set_ylim(0, 92)
axA.text(3.0, 44, "Separate live suite:\n96/96 refused", ha="center", va="bottom", fontsize=FS - 1.0, color=GREEN)
axA.plot([3.30, 3.30], [42.5, 0.9], color=GREEN, lw=0.9, zorder=4)  # leader runs beside the 0% label and ends on the group it points at
axA.plot([2.62, 3.38], [0, 0], color=GREEN, lw=2.2, solid_capstyle="butt", zorder=5)  # the zero-height group, drawn on the baseline
header(axA, "a  Declared checks and live record", "false-allow rate (%); 4 bars = 4 effect classes")

# ---- Panel b: cognitive safety limit ----
axB = fig.add_subplot(gs[1])
armorder = ["none", "generic", "induced"]
arm_labels = ["no\nmemory", "generic\ncaution", "induced\nprinciple"]
viol = [arms[a]["violation_rate"] * 100 for a in armorder]
over = [arms[a]["over_block_rate"] * 100 for a in armorder]
xb = np.arange(len(armorder))
axB.bar(xb - 0.2, viol, 0.38, color=VERMIL, label="red-line violation", edgecolor="white", lw=0.4)
axB.bar(xb + 0.2, over, 0.38, color=PURPLE, label="over-block\n(permitted failure)", edgecolor="white", lw=0.4)
for xi, v, o in zip(xb, viol, over):
    axB.text(xi - 0.2, v + 2, f"{v:.0f}", ha="center", va="bottom", fontsize=FS, color=VERMIL)
    axB.text(xi + 0.2, o + 2, f"{o:.0f}", ha="center", va="bottom", fontsize=FS, color=PURPLE)
axB.set_xticks(xb)
axB.set_xticklabels(arm_labels, fontsize=FS)
axB.set_ylim(0, 100)
axB.legend(frameon=False, fontsize=FS - 1.0, loc="upper left", bbox_to_anchor=(0.16, 1.0), handlelength=1.0)  # inside its own panel, clear of panel c
axB.set_xlim(-0.6, 2.6)
axB.text(2.58, 39, "lowest violation,\nhighest over-block", ha="right", va="bottom", fontsize=FS - 1.0, color="#333333")  # above the over-block bar and its value label, ending inside the panel; no leader
header(axB, "b  Two-endpoint tradeoff", "rate (%); Mistral-7B, 35 + 35 items")

# ---- Panel c: coverage bound (ceiling) ----
axC = fig.add_subplot(gs[2])
cats = ["within\nmodel", "cross-\nprovider", "config\nshift"]
dists = [att["within_model_max_distance"]["frontier_1"], att["cross_model_distance"], att["config_shift_max_distance"]["frontier_2"]]
assert dists == [0.0, 0.0, 0.0]
xc = np.arange(len(cats))
axC.plot(xc, [0, 0, 0], ls="", marker="o", ms=11, color=GREY, zorder=3)
for xi in xc:
    axC.text(xi, 1.1, "0", ha="center", va="bottom", fontsize=FS, fontweight="bold", color="#333333", zorder=4)
axC.set_xlim(-0.4, len(cats) - 0.6)  # the first marker sat on the y-axis spine at the default limits
axC.set_xticks(xc)
axC.set_xticklabels(cats, fontsize=FS)
axC.set_ylim(-1, 24)
axC.set_yticks([0, 6, 12, 18, 24])
axC.text(1.0, 13, "two frontier models,\n24/24 identical\nbaseline: 3 repeats\nconfig shift: 2", ha="center", va="center", fontsize=FS - 1.0,
         color="#333333", style="italic")
header(axC, "c  Fixed battery at ceiling", "fingerprint distance (of 24)")

fig.savefig(OUT / "fig_results.pdf", bbox_inches="tight")
fig.savefig(OUT / "fig_results.png", dpi=170, bbox_inches="tight")
print("wrote", OUT / "fig_results.pdf")
