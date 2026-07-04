"""R6 — the per-step cost of the governed-individuation machinery.

We time the three things the loop adds on top of the agent's own computation:
the governance check G, the identity digest H (the boot/step verification), and
the mediator fold M (effective_persona) at a few realization-layer sizes. All
are CPU operations independent of the model, so the overhead is the deployment
cost of governance, reported as microseconds (mean / p50 / p99).
"""

import json
import statistics
import time

from aeros.runtime.persona_core import PersonaCore
from aeros.runtime.persona_resolver import effective_persona

from gi.governance import AerosGovernance
from gi.identity import identity_digest
from gi.realization import RealizationLayer


def time_us(fn, n: int = 5000) -> dict:
    samples = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1e6)
    samples.sort()
    return {
        "mean_us": round(statistics.mean(samples), 2),
        "p50_us": round(samples[len(samples) // 2], 2),
        "p99_us": round(samples[int(len(samples) * 0.99)], 2),
    }


def main() -> None:
    core = PersonaCore(name="agent")
    gov = AerosGovernance(blocked_skills=["danger"])
    ctx = {"permissions": {"allowed_skills": None, "risk_level": "low", "actuators": ["arm"]}}

    def realization_events(k: int):
        layer = RealizationLayer(core)
        for i in range(k):
            layer.sediment_block(f"cap_{i}", reason=f"c{i}")
        return layer.events

    report = {
        "identity_digest_H": time_us(lambda: identity_digest(core)),
        "governance_G_check": time_us(lambda: gov("grasp", ctx)),
        "mediator_M_fold_R0": time_us(lambda: effective_persona(core, [])),
        "mediator_M_fold_R10": time_us(lambda ev=realization_events(10): effective_persona(core, ev)),
        "mediator_M_fold_R50": time_us(lambda ev=realization_events(50): effective_persona(core, ev)),
    }
    # total per-step governance overhead (G + H + M at R=10), p99
    per_step_p99 = (
        report["governance_G_check"]["p99_us"]
        + report["identity_digest_H"]["p99_us"]
        + report["mediator_M_fold_R10"]["p99_us"]
    )
    report["per_step_overhead_p99_us"] = round(per_step_p99, 2)
    report["per_step_overhead_p99_ms"] = round(per_step_p99 / 1000, 4)

    print(json.dumps(report, indent=2))
    json.dump(report, open("cost_result.json", "w"), indent=2)


if __name__ == "__main__":
    main()
