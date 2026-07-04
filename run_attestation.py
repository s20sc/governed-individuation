"""Behavioral-attestation go/no-go (local tier, 5090).

Fingerprints each local model K times (temperature>0 => benign nondeterminism), then compares:
  within-model distance  = mean pairwise fingerprint distance across a model's K runs (benign floor)
  cross-model distance   = fingerprint distance between different models (substitution signal)
Clean separation (within << cross) means behavioral attestation can detect a silent swap while a
name/version digest cannot. This is the local, reproducible tier; the cloud tier (codex/agy) is
run separately.
"""

import itertools
import json
import os

from gi.attest_probes import PROBES, build_prompt, fingerprint_distance, parse_choices
from gi.qwen_backend import QwenBackend

MODELS = [
    ("Qwen/Qwen2.5-7B-Instruct", "qwen7b"),
    ("mistralai/Mistral-7B-Instruct-v0.2", "mistral7b"),
    ("microsoft/Phi-3.5-mini-instruct", "phi35"),
]
K = 5
TEMPERATURE = 0.7


def main() -> None:
    prompt = build_prompt()
    prints = {}   # tag -> list of K fingerprints
    for path, tag in MODELS:
        backend = QwenBackend(path, temperature=TEMPERATURE)
        fps = []
        for seed in range(K):
            backend.seed(seed)
            fps.append(parse_choices(backend.generate(prompt)))
        prints[tag] = fps
        wr = [fingerprint_distance(a, b) for a, b in itertools.combinations(fps, 2)]
        wr = [d for d in wr if d == d]
        print(f"{tag}: within-model mean dist = {sum(wr)/len(wr):.3f} (n_pairs={len(wr)}, parsed {len(fps[0])}/{len(PROBES)})", flush=True)
        del backend

    # cross-model: use each model's run-0 fingerprint
    tags = [t for _, t in MODELS]
    cross = {}
    for a, b in itertools.combinations(tags, 2):
        d = fingerprint_distance(prints[a][0], prints[b][0])
        cross[f"{a}_vs_{b}"] = round(d, 3)
        print(f"cross {a} vs {b}: dist = {d:.3f}", flush=True)

    within = {t: round(sum(x for x in [fingerprint_distance(p, q) for p, q in itertools.combinations(prints[t], 2)] if x == x) /
                        max(1, len(list(itertools.combinations(prints[t], 2)))), 3) for t in tags}
    out = {"K": K, "temperature": TEMPERATURE, "n_probes": len(PROBES),
           "within_model_mean_dist": within, "cross_model_dist": cross,
           "fingerprints": {t: prints[t] for t in tags}}
    print(json.dumps({k: v for k, v in out.items() if k != "fingerprints"}, indent=2))
    json.dump(out, open("attestation_local.json", "w"), indent=2)


if __name__ == "__main__":
    main()
