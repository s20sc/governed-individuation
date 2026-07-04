"""ToolGym-GI spec-gaming inducement runner — the spec-gaming premise check.

Hard bugs + multi-turn pressure. Measures whether an ungoverned LLM spec-games
(edits the test to accept the buggy output) under repeated-failure pressure, and
whether the effect gate blocks that by EFFECT and forces continued real-fix work.
"""

import json
import os

from gi.qwen_backend import QwenBackend
from toolgym.hard import TASKS, run_hard

MODEL = os.environ.get("GI_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
TAG = os.environ.get("GI_TAG", "mistral7b")
SEEDS = list(range(12))
TEMPERATURE = 0.7


def main() -> None:
    backend = QwenBackend(MODEL, temperature=TEMPERATURE)
    rows = []
    for task in TASKS:
        for seed in SEEDS:
            for governed in (False, True):
                backend.seed(seed)
                r = run_hard(task, backend, governed=governed)
                r["seed"] = seed
                rows.append(r)
        u = [r for r in rows if r["task"] == task.name and not r["governed"]]
        g = [r for r in rows if r["task"] == task.name and r["governed"]]
        print(
            f"{task.name}: UNGOV spec-game {sum(x['spec_gamed'] for x in u)}/{len(u)} "
            f"realfix {sum(x['real_fix'] for x in u)}/{len(u)} tempted {sum(x['attempted_test_mutation'] for x in u)}/{len(u)} "
            f"| GOV spec-game {sum(x['spec_gamed'] for x in g)}/{len(g)} "
            f"realfix {sum(x['real_fix'] for x in g)}/{len(g)} tempted {sum(x['attempted_test_mutation'] for x in g)}/{len(g)}",
            flush=True,
        )

    def agg(gv):
        s = [r for r in rows if r["governed"] == gv]
        n = len(s)
        return {
            "n": n,
            "spec_game_rate": round(sum(r["spec_gamed"] for r in s) / n, 3),
            "real_fix_rate": round(sum(r["real_fix"] for r in s) / n, 3),
            "tempted_rate": round(sum(r["attempted_test_mutation"] for r in s) / n, 3),
            "pass_rate": round(sum(r["passed"] for r in s) / n, 3),
        }

    out = {"model": TAG, "ungoverned": agg(False), "governed": agg(True), "rows": rows}
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
    json.dump(out, open(f"toolgym_hard_{TAG}.json", "w"), indent=2)


if __name__ == "__main__":
    main()
