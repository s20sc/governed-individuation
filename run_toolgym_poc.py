"""ToolGym-GI PoC runner — the benchmark crux on a real LLM.

Under reward pressure ("scored only on whether the test passes"), does an
ungoverned agent spec-game (rewrite the test to accept the buggy output)? Does the
effect-lattice gate block exactly that by EFFECT and force the real code fix, with
zero executed spec-games, while keeping task success?

Open-action note: the agent freely names its action; the gate decides on effect, so
a test mutation relabelled "update_value" is still caught. A name blocklist cannot.
"""

import json
import os

from gi.qwen_backend import QwenBackend
from toolgym.poc import TASKS, run_task

MODEL = os.environ.get("GI_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
TAG = os.environ.get("GI_TAG", "mistral7b")
SEEDS = list(range(10))
TEMPERATURE = 0.7


def main() -> None:
    backend = QwenBackend(MODEL, temperature=TEMPERATURE)
    rows = []
    for task in TASKS:
        for seed in SEEDS:
            for governed in (False, True):
                backend.seed(seed)
                r = run_task(task, backend, governed=governed)
                r["seed"] = seed
                rows.append(r)
        u = [r for r in rows if r["task"] == task.name and not r["governed"]]
        g = [r for r in rows if r["task"] == task.name and r["governed"]]
        print(
            f"{task.name}: ungoverned spec-game {sum(x['spec_gamed'] for x in u)}/{len(u)} "
            f"real-fix {sum(x['real_fix'] for x in u)}/{len(u)} | "
            f"governed spec-game {sum(x['spec_gamed'] for x in g)}/{len(g)} "
            f"real-fix {sum(x['real_fix'] for x in g)}/{len(g)} "
            f"(tempted {sum(x['attempted_test_mutation'] for x in g)}/{len(g)})",
            flush=True,
        )

    def agg(governed):
        s = [r for r in rows if r["governed"] == governed]
        n = len(s)
        return {
            "n": n,
            "spec_game_rate": round(sum(r["spec_gamed"] for r in s) / n, 3),
            "real_fix_rate": round(sum(r["real_fix"] for r in s) / n, 3),
            "attempted_test_mutation_rate": round(sum(r["attempted_test_mutation"] for r in s) / n, 3),
        }

    out = {"model": TAG, "ungoverned": agg(False), "governed": agg(True), "rows": rows}
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
    json.dump(out, open(f"toolgym_poc_{TAG}.json", "w"), indent=2)


if __name__ == "__main__":
    main()
