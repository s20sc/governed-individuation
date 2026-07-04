"""The statistical study: GI vs Suppress over the scenario pool × seeds.

For each (scenario, seed) the two arms share the same sampling seed, so the only
difference is whether the realization layer's refusals reach the prompt. We
report a paired Wilcoxon test + effect size on the block rates, and the two
invariants that must hold across every run: identity is constant (I1) and the
number of landed actions outside the red-lines is zero (I2).
"""

import json
import os

from gi.proposer import LLMProposer
from gi.qwen_backend import QwenBackend
from gi.run import run_episodes
from gi.scenarios import SCENARIO_POOL
from gi.stats import paired_comparison

MODEL = os.environ.get("GI_MODEL", "Qwen/Qwen2.5-7B-Instruct")
TAG = os.environ.get("GI_TAG", "qwen7b")
SEEDS = [0, 1, 2, 3, 4]
TEMPERATURE = 0.7
N_STEPS = 8
N_WINDOWS = 4


def main() -> None:
    print(f"loading model {TAG} ({MODEL}, temp={TEMPERATURE}) ...", flush=True)
    backend = QwenBackend(MODEL, temperature=TEMPERATURE)

    rows = []
    for si, sc in enumerate(SCENARIO_POOL):
        for seed in SEEDS:
            try:
                backend.seed(seed)
                gi = run_episodes(sc, LLMProposer(backend, consult_realization=True), N_STEPS, N_WINDOWS)
                backend.seed(seed)
                sup = run_episodes(sc, LLMProposer(backend, consult_realization=False), N_STEPS, N_WINDOWS)
            except Exception as exc:  # noqa: BLE001 — one bad pair must not kill the run
                print(f"sc{si:02d} seed{seed}: SKIP ({type(exc).__name__})", flush=True)
                continue
            rows.append(
                {
                    "scenario": si,
                    "seed": seed,
                    "gi_block": gi.block_rate,
                    "sup_block": sup.block_rate,
                    "gi_id_const": gi.identity_constant,
                    "sup_id_const": sup.identity_constant,
                    "gi_viol": gi.permission_violations,
                    "sup_viol": sup.permission_violations,
                    "gi_windowed": gi.windowed_block_rate,
                }
            )
            print(f"sc{si:02d} seed{seed}: GI={gi.block_rate:.2f} Sup={sup.block_rate:.2f}", flush=True)

    gi_rates = [r["gi_block"] for r in rows]
    sup_rates = [r["sup_block"] for r in rows]
    stats = paired_comparison(gi_rates, sup_rates)

    triggering = [r for r in rows if r["sup_block"] > 0]  # pairs where a block actually occurs
    stats_triggering = paired_comparison(
        [r["gi_block"] for r in triggering], [r["sup_block"] for r in triggering]
    )

    invariants = {
        "identity_constant_all": all(r["gi_id_const"] and r["sup_id_const"] for r in rows),
        "total_permission_violations": sum(r["gi_viol"] + r["sup_viol"] for r in rows),
        "n_runs": len(rows) * 2,
        "n_pairs": len(rows),
        "n_triggering_pairs": len(triggering),
        "gi_mean_block": round(sum(gi_rates) / len(gi_rates), 4),
        "sup_mean_block": round(sum(sup_rates) / len(sup_rates), 4),
    }
    out = {"stats_all": stats, "stats_triggering": stats_triggering, "invariants": invariants, "rows": rows}
    print(json.dumps({"model": TAG, "stats_all": stats, "stats_triggering": stats_triggering, "invariants": invariants}, indent=2))
    json.dump(out, open(f"study_result_{TAG}.json", "w"), indent=2)


if __name__ == "__main__":
    main()
