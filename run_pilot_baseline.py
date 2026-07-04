"""Pilot — is the governed-individuation effect more than instruction-following?

Three arms differing ONLY in the feedback given after a refusal:
  specific = GI (the refused capability NAMES are surfaced; the paper's arm)
  generic  = fair baseline (told "you were refused, pick differently"; NO names)
  none     = suppress (no feedback)

The critique this pilot answers: the GI effect may be merely "the model obeys an explicit
'do not repeat X' instruction". The generic arm isolates that: if specific >> generic,
the realisation layer's specific memory matters; if specific ~= generic, the effect is
largely "any refusal signal helps" and the paper's framing must be downgraded.

Reports full-pool AND triggering-pair block rates for every arm (addressing the
post-selection critique too).
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
SEEDS = [0, 1, 2]
TEMPERATURE = 0.7
N_STEPS = 8


def main() -> None:
    print(f"loading {TAG} (temp={TEMPERATURE}) ...", flush=True)
    backend = QwenBackend(MODEL, temperature=TEMPERATURE)
    arms = ["specific", "generic", "none"]

    rows = []
    for si, sc in enumerate(SCENARIO_POOL):
        for seed in SEEDS:
            rec = {"scenario": si, "seed": seed}
            for fm in arms:
                backend.seed(seed)
                r = run_episodes(sc, LLMProposer(backend, feedback_mode=fm), N_STEPS, n_windows=4)
                rec[fm] = r.block_rate
            rows.append(rec)
            print(
                f"sc{si:02d} s{seed}: spec={rec['specific']:.2f} gen={rec['generic']:.2f} none={rec['none']:.2f}",
                flush=True,
            )

    spec = [r["specific"] for r in rows]
    gen = [r["generic"] for r in rows]
    non = [r["none"] for r in rows]

    def summ(a, b, label):
        trig = [(x, y) for x, y, n in zip(a, b, non) if n > 0]
        return {
            "label": label,
            "full": paired_comparison(a, b),
            "triggering": paired_comparison([x for x, _ in trig], [y for _, y in trig]) if trig else None,
            "n_trig": len(trig),
        }

    out = {
        "model": TAG,
        "arm_full_mean_block": {
            "specific": round(sum(spec) / len(spec), 3),
            "generic": round(sum(gen) / len(gen), 3),
            "none": round(sum(non) / len(non), 3),
        },
        "specific_vs_generic": summ(spec, gen, "GI(specific names) vs fair-baseline(generic)"),
        "generic_vs_none": summ(gen, non, "generic feedback vs suppress"),
        "specific_vs_none": summ(spec, non, "GI vs suppress (paper's original headline)"),
        "rows": rows,
    }
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2, default=str))
    json.dump(out, open(f"pilot_baseline_{TAG}.json", "w"), indent=2, default=str)


if __name__ == "__main__":
    main()
