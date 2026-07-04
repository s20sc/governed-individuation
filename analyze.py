"""Turn study_result.json into the headline figures (standalone PDFs) + a stats
summary. Figures are self-contained PDFs (CLAUDE.md figure rule); the main paper
includes them with \\includegraphics, never inline.
"""

import json
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = "figures"


def main() -> None:
    import os

    os.makedirs(OUT, exist_ok=True)
    d = json.load(open("study_result.json"))
    rows = d["rows"]
    gi = [r["gi_block"] for r in rows]
    sup = [r["sup_block"] for r in rows]

    # --- Figure A: paired block-rate contrast (GI vs Suppress) ---
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    ax.boxplot(
        [gi, sup],
        tick_labels=["Governed\nIndividuation", "Suppress\n(no feedback)"],
        widths=0.5,
    )
    ax.set_ylabel("blocked-proposal rate")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("Same model, same red-lines")
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig_block_rate_contrast.pdf")

    # --- Figure B: β_t decline (GI mean over triggering scenarios) vs Suppress flat ---
    trig = [r for r in rows if r["sup_block"] > 0]
    if trig:
        k = len(trig[0]["gi_windowed"])
        gi_curve = [statistics.mean(r["gi_windowed"][w] for r in trig) for w in range(k)]
        sup_curve = [1.0] * k
        fig, ax = plt.subplots(figsize=(3.4, 2.6))
        x = list(range(1, k + 1))
        ax.plot(x, gi_curve, "o-", label="Governed Individuation")
        ax.plot(x, sup_curve, "s--", label="Suppress")
        ax.set_xlabel("episode window")
        ax.set_ylabel(r"blocked-proposal rate $\beta_t$")
        ax.set_ylim(-0.05, 1.05)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(f"{OUT}/fig_beta_decline.pdf")

    # --- text summary ---
    print("=== STATS ===")
    print("all pairs      :", d["stats_all"])
    print("triggering only:", d["stats_triggering"])
    print("=== INVARIANTS ===")
    print(d["invariants"])


if __name__ == "__main__":
    main()
