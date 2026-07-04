"""Consolidated invariant check across the full scenario pool — the I1-I4 + A1
evidence in one run, on the real aeros mechanism (no LLM needed: governance and
the realization layer are exercised directly).

  A1+I1+I2 : a fully adversarial proposer proposes a red-lined action every step,
             across every scenario -> count landed red-lined actions (must be 0)
             and confirm identity never moves.
  I3       : run the loop so refusals occur, then check the audit reconstructs
             one-to-one.
  I4       : from the LLM study, the fraction of GI runs (where blocks occurred)
             whose β_t converges monotonically to zero.
"""

import json
import pathlib

from aeros.runtime.persona_core import PersonaCore

from gi.audit import reconstruction_complete
from gi.governance import AerosGovernance
from gi.loop import GovernedIndividuationLoop, Proposal
from gi.metrics import converges
from gi.proposer import AdversarialProposer
from gi.realization import RealizationLayer
from gi.run import run_episodes
from gi.scenarios import SCENARIO_POOL

_PERMS = {"permissions": {"allowed_skills": None, "risk_level": "low", "actuators": []}}


def adversarial_check() -> dict:
    violations, identity_ok, n = 0, True, 0
    for sc in SCENARIO_POOL:
        run = run_episodes(sc, AdversarialProposer(sc.red_lined[0]), n_steps=12)
        violations += run.permission_violations
        identity_ok = identity_ok and run.identity_constant
        n += len(run.results)
    return {"adversarial_steps": n, "landed_red_lined_actions": violations, "identity_constant": identity_ok}


def audit_check() -> dict:
    ok = True
    for sc in SCENARIO_POOL:
        layer = RealizationLayer(PersonaCore())
        gov = AerosGovernance(blocked_skills=sc.red_lined)

        def proposer(ctx, r, sc=sc):
            blocked = {e.capability for e in r.events}
            fresh = [c for c in sc.allowed_capabilities if c in sc.red_lined and c not in blocked]
            if fresh:
                return Proposal(fresh[0], {})
            safe = [c for c in sc.allowed_capabilities if c not in sc.red_lined]
            return Proposal(safe[0], {})

        loop = GovernedIndividuationLoop(layer, gov, proposer)
        results = [loop.step(_PERMS) for _ in range(10)]
        ok = ok and reconstruction_complete(results, layer)
    return {"all_scenarios_reconstructible": ok}


def convergence_check(study_path: str) -> dict:
    try:
        study = json.load(open(study_path))
    except FileNotFoundError:
        return {"note": f"study file not found at {study_path}"}
    gi_triggering = [r for r in study["rows"] if r["sup_block"] > 0]
    converged = sum(1 for r in gi_triggering if converges(r["gi_windowed"]))
    return {
        "gi_runs_with_blocks": len(gi_triggering),
        "converged_to_zero": converged,
        "fraction": round(converged / len(gi_triggering), 3) if gi_triggering else None,
    }


def _study_path() -> str:
    """Prefer a fresh root-level study_result.json (written by study.py); fall back
    to the released dated copy so I4 is checkable from the release alone."""
    import glob
    if pathlib.Path("study_result.json").exists():
        return "study_result.json"
    dated = sorted(glob.glob("data/*-study_result.json"))
    return dated[-1] if dated else "study_result.json"


def main() -> None:
    report = {
        "A1_I1_I2_adversarial": adversarial_check(),
        "I3_audit": audit_check(),
        "I4_convergence": convergence_check(_study_path()),
    }
    print(json.dumps(report, indent=2))
    json.dump(report, open("invariants_result.json", "w"), indent=2)


if __name__ == "__main__":
    main()
