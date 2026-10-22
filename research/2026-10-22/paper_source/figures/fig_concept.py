#!/usr/bin/env python3
"""Conceptual figure: one service life of a governable individual (Supplementary Figure 1).

Design notes (concrete artefacts rather than abstract boxes):
 - concrete artifacts: truncated digest hashes on the identity line, monospace
   admit/refuse stubs inside the gate bar, a concrete widening example;
 - the refused (widening) arrow is the visual star of the figure;
 - heterogeneous drift: weights drift slowly, memory churns, the skill library
   grows in discrete steps;
 - the digest line is an event timeline: one signed MODIFY step up (hand off),
   one committed-state rollback step down (roll back), hashes visibly change;
 - circled phase numbers; key phases emphasised.

Okabe-Ito palette; single semantic colour set (green=admitted, vermilion=refused/
signed events, black=identity digest). Standalone PDF per vault rule §7.12.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

BLUE = "#0072B2"
ORANGE = "#E69F00"
GREEN = "#009E73"
VERMIL = "#D55E00"
GREY = "#999999"
BLACK = "#000000"
MONO = {"family": "monospace"}

rng = np.random.default_rng(7)

fig, ax = plt.subplots(figsize=(11.5, 5.7))

X0, X1 = 0.0, 10.0
x = np.linspace(X0, X1, 900)

PHASES = [
    (0.0, "①", "boot", "#222222"),
    (1.5, "②", "learn", "#222222"),
    (3.0, "③", "consolidate", "#222222"),
    (4.5, "④", "acquire\nskill", "#222222"),
    (6.0, "⑤", "update\n(canary)", "#222222"),
    (7.25, "⑥", "federate", "#222222"),
    (8.575, "⑦", "hand off\n(new body /\nsupplier)", VERMIL),
    (9.9, "⑧", "roll\nback", VERMIL),
]

# ---------------- top lane: heterogeneous substrate drift ----------------
BASE = 3.15

# weights: slow drift
w_line = BASE + 0.35 * (x - X0) / (X1 - X0) + 0.12 * np.sin(0.7 * x + 0.4)

# memory: fast churn (smoothed deterministic noise over a mild trend)
noise = rng.normal(0, 1.0, x.size)
kern = np.ones(25) / 25.0
churn = np.convolve(noise, kern, mode="same")
m_line = BASE + 0.55 + 0.22 * (x - X0) / (X1 - X0) + 0.10 * churn + 0.05 * np.sin(3.1 * x)

# skill library: discrete growth (smooth staircase)
steps = [(1.5, 0.12), (3.0, 0.10), (4.5, 0.28), (6.0, 0.10), (7.25, 0.24)]  # one step per in-boundary event; a step at
# 9.1 matched no phase of the service life
s_line = np.full_like(x, BASE + 1.05)
for xs, h in steps:
    s_line += h * 0.5 * (1 + np.tanh((x - xs) * 9))

PURPLE = "#CC79A7"  # substrate variables use their own palette; green is reserved for admission
curves = [(w_line, BLUE, "weights (slow drift)"),
          (m_line, ORANGE, "memory (fast turnover)"),
          (s_line, PURPLE, "skill library (discrete growth)")]
for line, col, _ in curves:
    ax.plot(x, line, color=col, lw=2.2, alpha=0.9, solid_capstyle="round")
ends = sorted([(line[-1], col, label) for line, col, label in curves])
ys = [e[0] for e in ends]
for i in range(1, len(ys)):  # two labels closer than a box are spread about their midpoint, so each curve still ends
    if ys[i] - ys[i - 1] < 0.42:  # near its label's centre; pushing only the upper one up left the memory curve at a corner
        mid = (ys[i] + ys[i - 1]) / 2
        ys[i - 1], ys[i] = mid - 0.21, mid + 0.21
for y, (_, col, label) in zip(ys, ends):
    ax.text(X1 + 0.12, y, label, color="white", fontsize=11.5,
            va="center", ha="left", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.28", facecolor=col, edgecolor="none"))

ax.text(X0 - 0.15, BASE + 2.15, "COGNITIVE SUBSTRATE: drifts by design",
        fontsize=13.0, fontweight="bold", ha="left", va="bottom", color="#333333")

# ---------------- middle lane: boundary-contract gate ----------------
GATE_Y, GATE_H = 2.02, 0.40
# the bar starts in the left gutter, so its label sits wholly left of the first admitted lane (x=1.5): centred at 0.88
# the label ran across that lane, and its two lines filled the bar to within a pixel of both borders
ax.add_patch(Rectangle((-1.84, GATE_Y), X1 + 0.15 + 1.84, GATE_H,
                       facecolor="#EBEBEB", edgecolor=GREY, lw=1.2, zorder=2))
ax.text(-1.80, GATE_Y + GATE_H + 0.07, "BOUNDARY CONTRACT", fontsize=11.5, fontweight="bold",
        ha="left", va="bottom", color="#444444", zorder=7)
ax.text(-1.74, GATE_Y + GATE_H / 2, "admits by effect,\nnot by name",
        fontsize=11.5, ha="left", va="center", color="#444444", zorder=7, linespacing=0.9)  # 11.5 pt prints at the 6.5 pt floor
# concrete gate-decision stubs (ASPIRE lesson: real-looking artifacts)
# centred on the federation lane (x=7.25), the admitted event it records; at 7.75 it matched no event
ax.text(7.25, GATE_Y + GATE_H / 2, "✓ admit  read(shelf_map)",
        fontsize=12.5, color="#0B5F47", ha="center", va="center", zorder=8,
        bbox=dict(boxstyle="round,pad=0.28", facecolor="#E4F5EE", edgecolor=GREEN, lw=1.1), **MONO)
# wrapped onto two lines and centred on the refused event, so it sits in the column between the consolidate lane
# (x=3.0) and the canary lane (x=6.0): on one line it spanned both, and both ran behind its fill
# its top border kissed the bar's bottom border at GATE_Y - 0.27; a gap now shows it is a decision, not part of the bar
ax.text(4.5, GATE_Y - 0.33, "✗ refuse\nwrite(secrets/)",
        fontsize=12.5, color="#9A3E00", ha="center", va="center", zorder=8, linespacing=1.0,
        bbox=dict(boxstyle="round,pad=0.28", facecolor="#FBEAE0", edgecolor=VERMIL, lw=1.1), **MONO)

# ---------------- bottom lane geometry ----------------
DIG_Y0, DIG_Y1 = 0.80, 1.06
XM, XRB = 8.575, 9.9   # signed MODIFY (hand off); committed-state rollback

def action_arrow(xp, admitted=True):
    # below the vermilion annotation, not level with it: at the old height three of these arrows
    # ran through the sentence, visible in the gaps between letters even behind its box
    y_from = GATE_Y + GATE_H + 0.13
    if admitted:
        y_to = (DIG_Y1 if XM <= xp <= XRB else DIG_Y0) + 0.03
        ax.add_patch(FancyArrowPatch((xp, y_from), (xp, y_to),
                                     arrowstyle="-|>", mutation_scale=12,
                                     color=GREEN, lw=1.6, zorder=1))  # under the gate band, so the
        # admitted lane reads as passing THROUGH the contract rather than drawn across its border
    else:
        # the refused widening attempt: the visual star
        ax.add_patch(FancyArrowPatch((xp, 3.42), (xp, GATE_Y + GATE_H + 0.03),
                                     arrowstyle="-|>", mutation_scale=17,
                                     color=VERMIL, lw=3.2, zorder=6))
        ax.plot([xp - 0.20, xp + 0.20], [GATE_Y + GATE_H + 0.055] * 2,
                color=VERMIL, lw=3.4, zorder=6)

GREEN_XPS = [1.5, 3.0, 6.0, 7.25]
for xp in GREEN_XPS:
    action_arrow(xp, admitted=True)
# no legend here: beside the substrate curves it read as a label for the weights curve; the caption keys the green arrows

XW = 4.5
action_arrow(XW, admitted=False)
# committed-state rollback: a signed event that restores a previous digest (vermilion, not green)
# started level with the admitted arrows, below the annotation: at its old height it ran through
# the annotation's last word
# it ends above the step it points at: run down to the lower level it lay on the black riser and hid the restoring step
ax.add_patch(FancyArrowPatch((XRB, GATE_Y + GATE_H + 0.13), (XRB, DIG_Y1 + 0.08), arrowstyle="-|>", mutation_scale=12,
                             color=VERMIL, lw=1.6, zorder=4))
ax.text(XW + 0.28, GATE_Y + GATE_H + 0.20,
        "acquired skill requests secrets/access:\nwidening effect, refused unless signed",
        fontsize=11.5, color=VERMIL, ha="left", va="bottom", fontweight="bold",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.9, pad=1.5), zorder=7)

# ---------------- bottom lane: identity digest as an event timeline ----------------
seg_a = x[(x <= XM)]
seg_b = x[(x >= XM) & (x <= XRB)]
seg_c = x[(x >= XRB)]
ax.plot(seg_a, np.full_like(seg_a, DIG_Y0), color=BLACK, lw=3.0, solid_capstyle="round")
ax.plot([XM, XM], [DIG_Y0, DIG_Y1], color=BLACK, lw=3.0)
ax.plot(seg_b, np.full_like(seg_b, DIG_Y1), color=BLACK, lw=3.0, solid_capstyle="round")
ax.plot([XRB, XRB], [DIG_Y1, DIG_Y0], color=BLACK, lw=3.0)
ax.plot(seg_c, np.full_like(seg_c, DIG_Y0), color=BLACK, lw=3.0, solid_capstyle="round")

# in the left gutter with the other lane headings (BOUNDARY CONTRACT): spanning the lanes, its white box hid the
# learn and consolidate lanes on their way to the digest
ax.text(-1.80, 1.34, "IDENTITY DIGEST:\nH(commitment)",
        fontsize=13.0, fontweight="bold", ha="left", va="bottom", color="#333333", linespacing=1.0, zorder=8)

# concrete hashes (ASPIRE lesson: the mechanism, not the slogan)
# wholly left of the learn lane (x=1.5) and above the digest line, which its lower border rode on at va="top", y=1.06
ax.text(-1.80, DIG_Y0 + 0.12, "H = sha256:7f3a…c91", fontsize=13.0, color="#222222",
        ha="left", va="bottom", zorder=7, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#F0F0F0", edgecolor="#999999", lw=0.8), **MONO)
ax.text(X1 + 0.22, DIG_Y0 + 0.04, "…7f3a…c91 (restored)", fontsize=11.5,
        color="#222222", ha="left", va="bottom", zorder=7, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#F0F0F0", edgecolor="#999999", lw=0.8), **MONO)
ax.text(X1 + 0.22, DIG_Y0 - 0.075, "by committed-state rollback,\non the record", fontsize=13.0,
        color="#333333", ha="left", va="top", zorder=7,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.9, pad=1.0))

ax.text(4.5, DIG_Y0 + 0.07, "flat: in-boundary steps\nnever move the digest",  # in the gap between two action arrows, clear of the digest heading above
        fontsize=11.5, color="#333333", ha="center", va="bottom", zorder=7, linespacing=1.05)

# signed MODIFY: a concrete transaction stub card, directly above the hand-off marker
ax.plot([XM], [DIG_Y1 + 0.075], marker="v", color=VERMIL, ms=8, zorder=8)
# centred on the hand-off step, in the column between the federation lane (x=7.25) and the rollback lane
# (x=9.9): at x=9.6, right-aligned, it reached back over the federation lane, which ran behind its fill
ax.text(XM, 1.29,
        "MODIFY(body)\nsig: operator ✓\nnew H: 2b9e…4e2",
        fontsize=11.5, color="#9A3E00", ha="center", va="bottom", zorder=9, linespacing=1.0,
        bbox=dict(boxstyle="round,pad=0.32", facecolor="#FFF8F3", edgecolor=VERMIL, lw=1.2), **MONO)
ax.plot([XM, XM], [1.27, DIG_Y1 + 0.11], color=VERMIL, lw=1.0, ls=(0, (3, 2)), zorder=8)

# audit ticks at every gated event the lanes show, the refused one included: every step, admitted or refused, is on the record
for xp in [1.5, 3.0, 4.5, 6.0, 7.25]:
    ax.plot([xp], [DIG_Y0], marker="|", color=GREY, ms=9, mew=1.6, zorder=5)

# ---------------- phase axis with circled numbers ----------------
for i, (xp, num, lab, col) in enumerate(PHASES):
    badge_col = col if col != "#222222" else "#555555"
    ax.scatter([xp], [0.36], s=210, color=badge_col, zorder=6)
    ax.text(xp, 0.36, str(i + 1), fontsize=11.5, ha="center", va="center",
            color="white", fontweight="bold", zorder=7)
    ax.text(xp, 0.20, lab, fontsize=11.5, ha="center", va="top", color=col)
# it ran to X1 + 0.45, under a 90%-opaque caption box that starts at X1 + 0.12, so the head
# came out as a pale ghost between two lines of text, pointing at nothing
ax.add_patch(FancyArrowPatch((X0 - 0.15, 0.56), (X1 + 0.02, 0.56),  # at 0.52 the head sat on badge 8
                             arrowstyle="-|>", mutation_scale=12, color="#222222", lw=1.4))
ax.text(X0 - 0.25, 0.56, "service life", fontsize=11.5, ha="right", va="center", style="italic")  # at the tail of the axis it names;
# between phases 4 and 5 its ascenders rested on the digest line

# thesis line lives in the LaTeX caption (Nature convention), not in the artwork

ax.set_xlim(-1.85, 12.75)  # room for the left-hand labels clear of the curves, and for the end labels
ax.set_ylim(-0.62, 5.15)
ax.axis("off")
fig.tight_layout()

import pathlib
out = pathlib.Path(__file__).resolve().parent
fig.savefig(out / "fig_concept.pdf", bbox_inches="tight")
fig.savefig(out / "fig_concept.png", dpi=170, bbox_inches="tight")
fig.savefig((__import__("pathlib").Path(__file__).resolve().parent) / "fig_concept.svg", bbox_inches="tight")
print("wrote", out / "fig_concept.pdf")
