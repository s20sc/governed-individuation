#!/usr/bin/env python3
"""Supplementary Figure 2: the governed lifecycle.

Elliptical composition (an MLife-style
Machine Learning 2021, Fig. 3 is the reference), replacing the V1 circle; all
fonts sized for the final print width (drawn at 6.3 in, placed at 0.9\\linewidth,
so points here are points on the page).

At the centre sits the committed identity digest. Around it, the six lifecycle
functions of the text: five run autonomously and audited, leaving the digest
untouched (green); embodiment handoff & supplier swap touches the commitment and
can proceed only through a signed MODIFY that re-issues the digest (vermilion).

Okabe-Ito palette, cohesive with the other figures. Standalone PDF per §7.12.
"""

import pathlib

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, Ellipse, FancyArrowPatch, RegularPolygon, Wedge
from matplotlib.transforms import Affine2D

GREEN = "#009E73"
VERMIL = "#D55E00"
GREY = "#5A5A5A"
INK = "#222222"
MONO = {"family": "monospace"}

# function name, governance one-liner, whether it is the signed-MODIFY sector
SECTORS = [
    ("Epistemic adaptation", "consolidation may sharpen\nbehaviour, never widen authority", False),
    ("Capability\nacquisition", "skills enter by an\neffect-checked contract", False),
    ("Federation", "state crosses only\nthrough signed\nexport and import", False),
    ("Handoff, supplier swap,\ncommitted-state rollback", "the signed path: a new body,\nsubstrate or restored digest", True),
    ("Governed\nforgetting", "removal is signed,\naudited and\nreconstructable", False),
    ("Deployment,\nrecovery & replay", "canary and rollback\nleave the digest\nunchanged", False),
]

SX = 1.52          # horizontal stretch: circle -> ellipse (MLife-style oval)
r_in, r_out = 1.38, 3.06
N = len(SECTORS)
gap_deg = 2.6
start = 90         # first sector centred at the top

fig, ax = plt.subplots(figsize=(6.3, 4.62))
ax.set_aspect("equal")
oval = Affine2D().scale(SX, 1.0) + ax.transData

# outer "within the commitment" dashed boundary: an arc that opens at the signed sector, so the
# vermilion MODIFY wedge and its connector lie outside the "digest unchanged" region
i_mod = next(i for i, (_n, _o, m) in enumerate(SECTORS) if m)
a0_mod = start - i_mod * (360 / N) - (360 / N) / 2
a1_mod = start - i_mod * (360 / N) + (360 / N) / 2
ax.add_patch(Arc((0, 0), 2 * (r_out + 0.26) * SX, 2 * (r_out + 0.26),
                 theta1=a1_mod + 1.5, theta2=a0_mod - 1.5 + 360,
                 edgecolor=GREEN, lw=1.0, ls=(0, (2, 3)), alpha=0.7))

# per-sector label anchors (radius of the block centre, then hemisphere stacking)
R_MID = [2.46, 2.32, 2.32, 2.10, 2.24, 2.20]  # the two-line titles sit further in, clear of the outer arc
T_OFF = [0.16, 0.14, 0.14, 0.16, 0.14, 0.14]

for i, (name, oneliner, is_mod) in enumerate(SECTORS):
    a0 = start - i * (360 / N) - (360 / N) / 2 + gap_deg / 2
    a1 = start - i * (360 / N) + (360 / N) / 2 - gap_deg / 2
    mid = np.deg2rad((a0 + a1) / 2)
    col = VERMIL if is_mod else GREEN
    face = "#FBEDE4" if is_mod else "#E9F6F0"
    ax.add_patch(Wedge((0, 0), r_out, a0, a1, width=r_out - r_in,
                       facecolor=face, edgecolor=col, lw=1.5, zorder=2,
                       transform=oval))
    xa, ya = SX * R_MID[i] * np.cos(mid), R_MID[i] * np.sin(mid)
    tcol = VERMIL if is_mod else INK
    if np.sin(mid) >= -0.05:  # top & side sectors: title above description
        ax.text(xa, ya + T_OFF[i], name, ha="center", va="bottom",
                fontsize=9.0, fontweight="bold", color=tcol, zorder=4)
        ax.text(xa, ya + T_OFF[i] - 0.10, oneliner, ha="center", va="top",
                fontsize=7.8, color="#3A3A3A", zorder=4)
    else:                     # lower sectors: description above, title below (outer)
        ax.text(xa, ya - T_OFF[i], name, ha="center", va="top",
                fontsize=9.0, fontweight="bold", color=tcol, zorder=4)
        ax.text(xa, ya - T_OFF[i] + 0.10, oneliner, ha="center", va="bottom",
                fontsize=7.8, color="#3A3A3A", zorder=4)
    if is_mod:
        # a straight connector from the seal's edge to the signed sector's inner edge: no endpoint
        # shrinking, so the painted tip lands on the sector boundary rather than in the gap before it
        ax.add_patch(FancyArrowPatch((1.62 * np.cos(mid), 1.02 * np.sin(mid)),
                                     (SX * (r_in + 0.03) * np.cos(mid), (r_in + 0.03) * np.sin(mid)),
                                     arrowstyle="-|>", mutation_scale=11, shrinkA=0, shrinkB=0,
                                     color=VERMIL, lw=2.4, zorder=5))
        ax.plot([0, 0], [-r_out, -(r_out + 0.62)], color=VERMIL, lw=1.2, zorder=6)  # wedge edge to the callout box
        ax.text(0, -(r_out + 0.74), "signed MODIFY re-issues or restores the digest", ha="center", va="center",
                fontsize=8.2, fontweight="bold", color=VERMIL, zorder=6,
                bbox=dict(boxstyle="round,pad=0.32", facecolor="#FBEDE4",
                          edgecolor=VERMIL, lw=1.0))

# centre seal: committed identity digest
ax.add_patch(Ellipse((0, 0), 2 * 1.62, 2 * 1.02,
                     facecolor="#F2F2F2", edgecolor=INK, lw=2.0, zorder=6))
ax.text(0, 0.42, "identity digest", ha="center", va="center", fontsize=9.2,
        fontweight="bold", color=INK, zorder=7)
ax.text(0, 0.12, "H(commitment)", ha="center", va="center", fontsize=8.4, color=INK, zorder=7)
ax.text(0, -0.18, "sha256:7f3a…c91", ha="center", va="center", fontsize=7.6,
        color="#333333", zorder=7, **MONO)
ax.text(0, -0.46, "frozen · public · signed", ha="center", va="center", fontsize=7.2,
        color=GREY, style="italic", zorder=7)

# green ring caption (top)
ax.text(0, r_out + 0.56, "within the commitment (dashed): autonomous, audited, digest unchanged",
        ha="center", va="center", fontsize=8.6, color=GREEN, fontweight="bold")

ax.set_xlim(-(r_out + 0.30) * SX, (r_out + 0.30) * SX)
ax.set_ylim(-(r_out + 1.05), r_out + 0.90)
ax.axis("off")
fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)

out = pathlib.Path(__file__).resolve().parent
fig.savefig(out / "fig_lifecycle.pdf", bbox_inches="tight")
fig.savefig(out / "fig_lifecycle.png", dpi=170, bbox_inches="tight")
fig.savefig(out / "fig_lifecycle.svg", bbox_inches="tight")
print("wrote", out / "fig_lifecycle.pdf")
