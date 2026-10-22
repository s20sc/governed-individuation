"""Two finite evidence readouts, drawn from the reviewed offline analysis JSON."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / "analysis-output-final" / "analysis.json"
raw = DATA.read_bytes()
manifest_input = json.loads(DATA.with_name("manifest.json").read_text())
if hashlib.sha256(raw).hexdigest() != manifest_input["analysis_sha256"]:
    raise ValueError("analysis bytes differ from retained manifest")
data = json.loads(raw)


def require(condition, message):
    if not condition:
        raise ValueError(message)

observation = {"condition": "reference", "test_id": "test-2-Kestrel", "choice": "admit"}
matches = [c for c in data["item_projection"]["class_records"] if c["observation"] == observation]
require(len(matches) == 1, "expected one witness class")
members = sorted(matches[0]["members"], key=lambda r: r["block"])
require(len(members) == 2 and [r["block"] for r in members] == [0, 3], "unexpected witness blocks")
require([r["literal_status"] for r in members] == ["contradicts_supplied", "agrees_with_supplied"], "unexpected local statuses")
require(all(r["choice"] == r["supplied_choice"] == "admit" for r in members), "unexpected witness choices")
require([(r["owned"], r["public"]) for r in members] == [(True, False), (True, False)], "unexpected witness attributes")
readouts = {r["arm"]: r for r in data["target_readouts"]}
require(all(readouts[a]["n"] == 32 for a in ("direct-flipped", "generated-flipped")), "unexpected arm size")

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "axes.spines.top": False, "axes.spines.right": False,
})
ink, muted = "#222222", "#595959"
blue, purple, green, red = "#0072B2", "#A35F91", "#007A5E", "#BB4A00"
fig = plt.figure(figsize=(7.0, 5.5), facecolor="white")
fig.text(.04, .965, "A   Same observed answer; different local clause fidelity",
         fontsize=11, fontweight="bold", color=ink, va="top")
ax = fig.add_axes([.04, .515, .92, .395])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
ax.add_patch(FancyBboxPatch((.035, .715), .93, .24,
    boxstyle="round,pad=0.015", facecolor="#F1F3F4", edgecolor="#B7BDC1", lw=.8))
ax.text(.5, .867, "Retained observation: reference condition, Kestrel test item, choice = admit",
        ha="center", va="center", fontsize=9, color=ink)
ax.text(.5, .777, "Query: owned = true, public = false; supplied mapping requires admit",
        ha="center", va="center", fontsize=8.7, color=muted)
for x, row, col in zip((.035, .525), members, (red, green)):
    ax.add_patch(FancyBboxPatch((x, .075), .44, .535,
        boxstyle="round,pad=0.015", facecolor="white", edgecolor=col, lw=1.3))
    ax.text(x+.22, .53, "Recorded rule: block " + str(row["block"]),
            ha="center", va="center", fontsize=9.3, fontweight="bold", color=ink)
    ax.text(x+.22, .40, "Local constraint: " + row["constraint"][0].upper(),
            ha="center", va="center", fontsize=10, color=col, fontweight="bold")
    ax.text(x+.22, .285, "Final choice: " + row["choice"].upper(),
            ha="center", va="center", fontsize=9.3, color=blue)
    verdict = "Local clause conflicts with mapping" if row["literal_status"] == "contradicts_supplied" else "Local clause matches mapping"
    ax.text(x+.22, .16, verdict, ha="center", va="center", fontsize=8.4, color=col)
ax.text(.5, -.015, "Rule text, block and seed are omitted by this observation projection.",
        ha="center", va="center", fontsize=8.2, color=muted)

fig.text(.04, .445, "B   Same flipped-condition choices; different scoring targets",
         fontsize=11, fontweight="bold", color=ink, va="top")
bx = fig.add_axes([.12, .12, .83, .265])
centres = [0, 1]
width = .26
series = [
    ("direct-flipped", "Direct examples", blue, -.15),
    ("generated-flipped", "Generated rules", purple, .15),
]
for arm, label, colour, offset in series:
    values = [readouts[arm]["supplied_mapping_agreements"],
              readouts[arm]["fixed_reference_agreements"]]
    bars = bx.bar([c+offset for c in centres], values, width,
                  label=label, color=colour, zorder=3)
    for bar, value in zip(bars, values):
        bx.text(bar.get_x()+bar.get_width()/2, value+.7, str(value)+"/32",
                ha="center", va="bottom", fontsize=9, color=ink)
bx.set_xticks(centres, ["Supplied mapping", "Fixed experimental reference"])
bx.set_ylim(0, 32)
bx.set_yticks([0, 8, 16, 24, 32])
bx.set_ylabel("Agreements / 32 decisions", fontsize=8.6, rotation=0, ha="left", va="bottom")
bx.yaxis.set_label_coords(-.02, 1.035)
bx.grid(axis="y", color="#E1E4E6", lw=.6, zorder=0)
bx.set_axisbelow(True)
bx.tick_params(axis="both", labelsize=8.5)
bx.legend(loc="upper center", bbox_to_anchor=(.55, 1.0), ncol=2,
          frameon=False, fontsize=8.4)
fig.text(.5, .035, "Complementary target labels account for the reversal; neither target authenticates authority.",
         ha="center", fontsize=8.1, color=muted)
pdf, png = HERE/"fig_observation_contracts.pdf", HERE/"fig_observation_contracts.png"
fig.savefig(pdf, metadata={"Creator": "P-Finale offline reanalysis", "CreationDate": None, "ModDate": None})
fig.savefig(png, dpi=180)
plt.close(fig)
manifest = {
    "input": str(DATA.relative_to(HERE.parents[1])),
    "input_sha256": hashlib.sha256(raw).hexdigest(),
    "item_observation": observation, "member_ids": [r["id"] for r in members],
    "outputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (pdf, png)},
    "scope": "Existing finite records and explicit annotation inputs; no causal path, new response or authority validation.",
}
(HERE/"fig_observation_contracts.manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
