"""One-command reproduction of the governed-individuation experiments.

Stages (each prints a PASS/data line):
  1. unit tests          — the harness invariants in isolation
  2. invariant check     — I1-I4 + adversarial on the full scenario pool (no model)
  3. cost benchmark      — per-step governance overhead
  4. statistical study   — GI vs Suppress over the scenario pool x seeds (needs the model)
  5. figures             — the headline PDFs

Usage:
    PYTHONPATH=<aeros-src>:. python reproduce.py            # full run
    PYTHONPATH=<aeros-src>:. python reproduce.py --no-model # skip the LLM study

The model study needs a local Qwen2.5-7B-Instruct at the path in study.py; the
mechanism-only stages (1-3) run on CPU in seconds and already establish I1-I4.
"""

import subprocess
import sys

NO_MODEL = "--no-model" in sys.argv


def run(label: str, cmd: list[str]) -> bool:
    print(f"\n=== {label} ===", flush=True)
    proc = subprocess.run(cmd)
    ok = proc.returncode == 0
    print(f"--- {label}: {'PASS' if ok else 'FAIL'} (rc={proc.returncode}) ---", flush=True)
    return ok


def main() -> int:
    py = sys.executable
    steps = [
        ("unit tests", [py, "-m", "pytest", "tests/", "-q"]),
        ("invariant check (I1-I4 + adversarial)", [py, "verify_invariants.py"]),
        ("cost benchmark (R6)", [py, "bench_cost.py"]),
    ]
    if not NO_MODEL:
        steps.append(("statistical study (GI vs Suppress)", [py, "study.py"]))
        steps.append(("figures", [py, "analyze.py"]))

    results = {label: run(label, cmd) for label, cmd in steps}
    print("\n==== SUMMARY ====")
    for label, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
