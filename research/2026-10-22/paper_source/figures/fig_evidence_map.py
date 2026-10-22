"""Conceptual evidence map; arrows name recorded interfaces, not causal effects."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "pdf.fonttype": 42})
fig, ax = plt.subplots(figsize=(7.0, 4.25))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
blue, ink, grey = "#0072B2", "#222222", "#60666A"


def card(x, y, w, h, title, body, dashed=False, colour=blue):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.009",
        facecolor="white" if dashed else "#F1F7FA", edgecolor=colour,
        linewidth=1.1, linestyle=(0, (4, 2)) if dashed else "solid"))
    ax.text(x+w/2, y+h-.052, title, ha="center", va="center",
            fontsize=9.4, fontweight="bold", color=ink)
    ax.text(x+w/2, y+h/2-.027, body, ha="center", va="center",
            fontsize=8.5, linespacing=1.4, color=grey)


ax.text(.025, .965, "A   Generated-rule path: retained inputs, text and choices",
        fontweight="bold", fontsize=10.6, va="top", color=ink)
xs = [.025, .275, .525, .775]
titles = ["Mapping M", "Rule text R", "Choice Y", "Scoring target"]
bodies = ["Supplied labels\non examples", "Explicit local\nconstraints", "Parsed admit /\ndefer response", "Compare Y with M\nor fixed reference"]
for x, title, body in zip(xs, titles, bodies):
    card(x, .68, .20, .205, title, body)
for left, right in zip(xs[:-1], xs[1:]):
    ax.add_patch(FancyArrowPatch((left+.207, .782), (right-.010, .782),
        arrowstyle="-|>", mutation_scale=10, linewidth=.9, color=grey))
ax.text(.5, .625, "Recorded inputs and outputs; the arrows do not identify internal mediation.",
        ha="center", fontsize=8.2, color=grey)
ax.plot([.025, .975], [.565, .565], color="#D7DCDF", linewidth=.8)
ax.text(.025, .525, "B   Execution claims: authority, interface and effect obligations",
        fontweight="bold", fontsize=10.6, va="top", color=ink)
card(.025, .245, .285, .20, "Authorised boundary S",
     "Independent source and\napplicability required", dashed=True, colour="#B66000")
card(.358, .245, .285, .20, "Interface records",
     "Digest, declared targets,\nreported operations")
card(.69, .245, .285, .20, "Relevant effects E",
     "Complete execution effects\nnot jointly established", dashed=True, colour=grey)
ax.text(.5, .18, "Authority claims additionally require protected state, complete mediation and sound effect abstraction.",
        ha="center", fontsize=8.05, color=ink)
ax.text(.5, .105, "Solid fields occur in retained studies; dashed requirements are not established by the advice pilot.",
        ha="center", fontsize=8, color=grey)
ax.text(.5, .055, "The mechanism studies use separate implementations; the diagram is not one evaluated lifecycle.",
        ha="center", fontsize=8, color=grey)
fig.subplots_adjust(left=.01, right=.99, top=.99, bottom=.01)
out = Path(__file__).resolve().parent
fig.savefig(out/"fig_evidence_map.pdf", metadata={"CreationDate": None, "ModDate": None})
fig.savefig(out/"fig_evidence_map.png", dpi=180)
plt.close(fig)
