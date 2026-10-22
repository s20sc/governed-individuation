#!/usr/bin/env python3
"""Supplementary Figure 3: the specified reference monitor between substrate and identity layer.

A reference-monitor data-flow diagram: how the boundary-contract gate mediates every
proposed action at runtime. The drifting neural substrate proposes an action; the
runtime monitor intercepts it; a semantic-effect verifier resolves what the action
would actually do; the effect is checked against the frozen boundary commitment
(whose hash is the identity digest); the action is admitted (and appended to the
signed audit chain) or refused. Relax-direction changes require operator-signed
MODIFY; pure tightening is permitted by the specification but omitted here.
The fixed-commitment prototype implements neither transition route.

Shows concretely "how the reference monitor works at
runtime" figure. Okabe-Ito palette, cohesive with the other figures. Standalone PDF.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

GREEN = "#009E73"
VERMIL = "#D55E00"
BLUE = "#0072B2"
INK = "#222222"
GREY = "#666666"
MONO = {"family": "monospace"}

fig, ax = plt.subplots(figsize=(11.0, 6.4))
ax.set_xlim(0, 106.6)  # margin to the right of the return path and the caption above it
ax.set_ylim(0, 100)
ax.axis("off")


def box(x, y, w, h, text, edge, face, fs=9.5, bold=True, mono=False, zorder=3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=2.2",
                                linewidth=1.8, edgecolor=edge, facecolor=face, zorder=zorder))
    kw = dict(ha="center", va="center", fontsize=fs, color=INK, zorder=zorder + 1)
    if bold:
        kw["fontweight"] = "bold"
    if mono:
        kw["family"] = "monospace"
    ax.text(x + w / 2, y + h / 2, text, **kw)


def arrow(x0, y0, x1, y1, color=INK, lw=2.0, style="-|>", ms=15, rad=0.0, z=2):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=ms,
                                 color=color, lw=lw, zorder=z, shrinkA=0, shrinkB=0,
                                 connectionstyle=f"arc3,rad={rad}"))


NEUTRAL = "#6A6A6A"   # substrate and monitor stages are neutral; green/vermilion mark outcomes only
NFACE = "#F4F4F4"


def lbl(x, y, text, color=GREY, fs=9.5, style="normal", ha="center", mono=False):
    kw = dict(ha=ha, va="center", fontsize=fs, color=color, style=style, zorder=6)
    if mono:
        kw["family"] = "monospace"
    ax.text(x, y, text, **kw)


# ---- lane titles ----
lbl(15, 96, "COGNITIVE SUBSTRATE", color="#333333", fs=10.5)
lbl(15, 92.5, "(mutable, learns)", color=GREY, fs=9.5)
lbl(85.5, 96, "IDENTITY LAYER", color="#333333", fs=10.5)
lbl(85.5, 92.5, "(frozen, committed)", color=GREY, fs=9.5)
ax.text(50, 96.5, "RUNTIME REFERENCE MONITOR", ha="center", va="center", fontsize=10.5,
        fontweight="bold", color="#333333")

# ---- substrate (left): neutral, it is neither admitted nor refused ----
box(3, 74, 24, 8, "neural policy\n(weights)", NEUTRAL, NFACE, fs=10)
box(3, 60, 24, 8, "skill library", NEUTRAL, NFACE, fs=10, bold=False)
box(3, 44.5, 24, 8, "episodic memory", NEUTRAL, NFACE, fs=10, bold=False)

# ---- identity layer (right) ----
box(73, 59, 25, 10, "boundary\ncommitment $S$", BLUE, "#E6F2F7", fs=11)
box(73, 44, 25, 9, "identity digest\nH(commitment)", INK, "#F0F0F0", fs=10.5)
lbl(85.5, 41.2, "sha256:7f3a…c91", color="#333333", fs=9.5, mono=True)

# ---- monitor (centre column), top to bottom: neutral stages ----
box(37, 74, 26, 8, "1  intercept\nproposed action", NEUTRAL, NFACE, fs=9.8)
box(37, 60, 26, 8, "2  semantic-effect\nverifier", NEUTRAL, NFACE, fs=9.8)
box(37, 44, 26, 9, "3  check effect vs\ncommitment", NEUTRAL, "#EAEAEA", fs=9.8)

# ---- outcomes (bottom) ----
box(6, 20, 27, 9, "ADMIT\naction executes", GREEN, "#E4F5EE", fs=9.5)
box(6, 6, 27, 8, "signed audit chain\n(append-only)", GREEN, "#E4F5EE", fs=9.5, bold=False)
box(67, 20, 27, 9, "REFUSE\nwidening effect", VERMIL, "#FBEDE4", fs=9.5)
box(67, 6, 27, 8, "operator MODIFY\n(signs new $S$, $H$)", VERMIL, "#FBEDE4", fs=9.5, bold=False, mono=False)

# ---- flows ----
# substrate proposes -> intercept
arrow(27.62, 78, 36.38, 78, color=NEUTRAL, lw=2.0)
lbl(24.0, 71.0, "proposes action", color=NEUTRAL, fs=9.5, ha="center")  # wholly left of the dashed monitor bracket (its edge is x=33.9)
# intercept -> verifier -> check
arrow(50, 73.38, 50, 68.62, color=NEUTRAL, lw=2.0)
arrow(50, 59.38, 50, 53.62, color=NEUTRAL, lw=2.0)
# check <-> commitment (compare against ceiling)
ax.plot([63.62, 68.0, 68.0, 72.38], [48.5, 48.5, 64.0, 64.0], color=BLUE, lw=1.8,  # one connector,
        solid_joinstyle="miter", solid_capstyle="butt", zorder=2)  # with a head only at each end
arrow(70.9, 64.0, 72.38, 64.0, color=BLUE, lw=1.8)   # into the commitment box
arrow(65.1, 48.5, 63.62, 48.5, color=BLUE, lw=1.8)   # and back into the check box
lbl(69.3, 56.4, "compare with $S$", color=BLUE, fs=9.5, ha="left")  # one line in the band between the two
# boxes (their drawn borders are y=58.4 and y=53.6), left-anchored just right of the vertical run at x=68
# commitment -> digest (hashes to)
arrow(85.5, 58.42, 85.5, 53.62, color=INK, lw=1.6)
lbl(87.4, 56.3, "hashes to", color=GREY, fs=9.5, ha="left")  # right of its arrow, clear of the label beside the connector
# check -> admit (green): orthogonal elbow, down from the gate, left along a bus, down into ADMIT
ax.plot([43, 43, 19.5], [43.38, 36, 36], color=GREEN, lw=2.2, solid_joinstyle="miter", solid_capstyle="butt", zorder=2)
arrow(19.5, 36, 19.5, 29.62, color=GREEN, lw=2.2)
lbl(31.5, 38.6, "within boundary", color=GREEN, fs=9.5)
# admit -> audit
arrow(19.5, 19.38, 19.5, 14.62, color=GREEN, lw=1.8)
# check -> refuse (vermilion): orthogonal elbow, down from the gate, right along a bus, down into REFUSE
ax.plot([57, 57, 80.5], [43.38, 36, 36], color=VERMIL, lw=2.6, solid_joinstyle="miter", solid_capstyle="butt", zorder=2)
arrow(80.5, 36, 80.5, 29.62, color=VERMIL, lw=2.6)
lbl(68.5, 38.6, "widens authority", color=VERMIL, fs=9.5)
# refuse -> modify (only path to change S)
arrow(80.5, 19.38, 80.5, 14.62, color=VERMIL, lw=1.6, style="-|>")
# modify -> commitment (the ONLY channel that changes S/H) -- long vermilion up the right
ax.plot([94.62, 101.3, 101.3, 99.9], [10, 10, 64, 64], color=VERMIL, lw=2.4,
        solid_joinstyle="miter", solid_capstyle="butt", zorder=4)
ax.add_patch(FancyArrowPatch((100.0, 64), (98.62, 64), arrowstyle="-|>", mutation_scale=11,
                             color=VERMIL, lw=2.4, shrinkA=0, shrinkB=0, zorder=4))
# two lines: on one line this label reached x=65.6 and crossed the monitor bracket's right edge (x=66.6)
ax.text(84.2, 73.8, "authorised route for\nrelax-direction changes",
        color=VERMIL, fontsize=9.5, style="italic", ha="center", va="center", zorder=6,
        linespacing=1.15)

# monitor bracket (subtle background)
ax.add_patch(FancyBboxPatch((34.5, 41.5), 31.5, 43, boxstyle="round,pad=0.6,rounding_size=3",
                            linewidth=1.0, edgecolor="#BBBBBB", facecolor="none",
                            linestyle=(0, (3, 3)), zorder=1))

import pathlib
out = pathlib.Path(__file__).resolve().parent
fig.savefig(out / "fig_architecture.pdf", bbox_inches="tight")
fig.savefig(out / "fig_architecture.png", dpi=170, bbox_inches="tight")
print("wrote", out / "fig_architecture.pdf")
