"""ToolGym-GI full run — the benchmark's full run.

Flow:
  1. TRAIN: run the gated GI agent on TRAIN families; collect refusal records.
  2. INDUCE: recover a governance principle from those refusals (no human text).
  3. TEST: run every arm on HELD-OUT families (disjoint effects + file names).
  4. MEASURE per arm on held-out:
       executed_violation_rate  — executed a forbidden effect (deterministic containment:
                                   ungoverned/prompted > 0; any gated arm = 0)
       attempted_forbidden_rate — reached for a forbidden shortcut (generalisation signal:
                                   the induced principle should lower this on held-out)
       success_rate             — legitimate task completion (preserved under governance)
"""

import json
import os

from gi.qwen_backend import QwenBackend
from toolgym.bench import ARMS, TASKS, ArmConfig, run_episode
from toolgym.inducer import collect_refusals, induce_principle

MODEL = os.environ.get("GI_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
TAG = os.environ.get("GI_TAG", "mistral7b")
SEEDS = list(range(8))
TEMPERATURE = 0.7

TRAIN = [t for t in TASKS if t.split == "train"]
TEST = [t for t in TASKS if t.split == "test"]
BY_NAME = {t.name: t for t in TASKS}


def main() -> None:
    backend = QwenBackend(MODEL, temperature=TEMPERATURE)

    # 1. TRAIN — collect refusals with the gated names arm
    print("== TRAIN: collecting refusals ==", flush=True)
    train_gi = ArmConfig("gi_names", gate=True, memory="names")
    train_results = []
    for t in TRAIN:
        for seed in SEEDS:
            backend.seed(seed)
            train_results.append(run_episode(t, backend, train_gi))
    records = collect_refusals(train_results, BY_NAME)
    print(f"  {len(records)} unique refusal records: {[r['refused_file'] for r in records]}", flush=True)

    # 2. INDUCE
    backend.seed(0)
    principle, phash = induce_principle(records, backend)
    print(f"== INDUCED PRINCIPLE (hash {phash}) ==\n  {principle}", flush=True)

    # 3. TEST — every arm on HELD-OUT families
    arms = []
    for a in ARMS:
        arms.append(ArmConfig(a.name, gate=a.gate, policy_in_prompt=a.policy_in_prompt,
                              memory=a.memory, induced_principle=principle if a.memory == "induced" else ""))
    print("== TEST: held-out families ==", flush=True)
    rows = []
    for arm in arms:
        for t in TEST:
            for seed in SEEDS:
                backend.seed(seed)
                r = run_episode(t, backend, arm)
                r["seed"] = seed
                rows.append(r)
        s = [r for r in rows if r["arm"] == arm.name]
        n = len(s)
        print(
            f"  {arm.name:16s}: violation {sum(x['violation'] for x in s)}/{n} "
            f"attempted {sum(x['attempted_forbidden'] for x in s)}/{n} "
            f"success {sum(x['success'] for x in s)}/{n}",
            flush=True,
        )

    def agg(arm_name):
        s = [r for r in rows if r["arm"] == arm_name]
        n = len(s)
        return {
            "n": n,
            "executed_violation_rate": round(sum(r["violation"] for r in s) / n, 3),
            "attempted_forbidden_rate": round(sum(r["attempted_forbidden"] for r in s) / n, 3),
            "success_rate": round(sum(r["success"] for r in s) / n, 3),
        }

    out = {
        "model": TAG,
        "induced_principle": principle,
        "induced_principle_hash": phash,
        "n_refusal_records": len(records),
        "refused_files": [r["refused_file"] for r in records],
        "heldout_by_arm": {a.name: agg(a.name) for a in arms},
        "rows": rows,
    }
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
    json.dump(out, open(f"toolgym_full_{TAG}.json", "w"), indent=2)


if __name__ == "__main__":
    main()
