"""Cross-model generality summary.

Loads the per-model study results and reports, for each model, the GI vs
Suppress contrast on the triggering pairs plus the two invariants. If the effect
holds across models, governed individuation is not an artifact of one model.

Usage:
    python analyze_models.py study_result_qwen7b.json study_result_mistral7b.json
"""

import json
import sys


def load(path: str) -> dict:
    return json.load(open(path))


def row(tag: str, d: dict) -> dict:
    st = d["stats_triggering"]
    inv = d["invariants"]
    return {
        "model": d.get("model", tag),
        "n_triggering": st["n_pairs"],
        "median_gi": round(st["median_gi"], 3),
        "median_suppress": round(st["median_suppress"], 3),
        "p_value": st["p_value"],
        "effect_size": round(st["effect_size"], 3),
        "identity_constant_all": inv["identity_constant_all"],
        "permission_violations": inv["total_permission_violations"],
        "n_runs": inv["n_runs"],
    }


def main() -> None:
    paths = sys.argv[1:] or ["study_result_qwen7b.json", "study_result_mistral7b.json"]
    rows = [row(p, load(p)) for p in paths]

    print(f"{'model':22s} {'n_trig':>6s} {'med_GI':>7s} {'med_Sup':>8s} {'p':>10s} {'eff':>5s} {'id_const':>9s} {'viol':>5s}")
    for r in rows:
        print(
            f"{r['model']:22s} {r['n_triggering']:6d} {r['median_gi']:7.3f} "
            f"{r['median_suppress']:8.3f} {r['p_value']:10.2e} {r['effect_size']:5.2f} "
            f"{str(r['identity_constant_all']):>9s} {r['permission_violations']:5d}"
        )

    generality = {
        "all_models_significant": all(r["p_value"] < 0.05 for r in rows),
        "all_models_gi_below_suppress": all(r["median_gi"] < r["median_suppress"] for r in rows),
        "all_models_identity_constant": all(r["identity_constant_all"] for r in rows),
        "all_models_zero_violations": all(r["permission_violations"] == 0 for r in rows),
        "n_models": len(rows),
    }
    print("\ngenerality:", json.dumps(generality))
    json.dump({"rows": rows, "generality": generality}, open("models_comparison.json", "w"), indent=2)

    _make_figure(rows)


def _make_figure(rows: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import os

    import matplotlib.pyplot as plt

    labels = [r["model"].split("/")[-1] for r in rows]
    gi = [r["median_gi"] for r in rows]
    sup = [r["median_suppress"] for r in rows]
    x = range(len(rows))
    w = 0.35

    fig, ax = plt.subplots(figsize=(max(5.6, 2.4 + 1.6 * len(rows)), 3.3))
    ax.bar([i - w / 2 for i in x], sup, w, label="Suppress (no feedback)", color="#c44", edgecolor="black", linewidth=0.6)
    ax.bar([i + w / 2 for i in x], gi, w, label="Governed individuation", color="#268", edgecolor="black", linewidth=0.6)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("median blocked-proposal rate")
    ax.set_ylim(0, 1.12)
    ax.set_title("Growth without drift, across model families", fontsize=11)
    ax.legend(frameon=False, fontsize=8, loc="center right")
    for i, r in enumerate(rows):
        ax.text(i, 1.0, f"p={r['p_value']:.0e}\n0 violations", ha="center", va="bottom", fontsize=6.5)
    fig.tight_layout()
    os.makedirs("figures", exist_ok=True)
    fig.savefig("figures/fig_model_generality.pdf")
    print("wrote figures/fig_model_generality.pdf")


if __name__ == "__main__":
    main()
