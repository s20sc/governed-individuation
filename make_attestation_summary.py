#!/usr/bin/env python3
"""Regenerate data/2026-07-02-attestation-summary.json from the raw frontier responses.

Checked in so the "assert-guarded" claim in the SI is verifiable: the asserts below
fail loudly if the raw data ever disagrees with the numbers reported in the paper.
Run from experiments/gi/:  python3 make_attestation_summary.py
"""

import json
import pathlib
import re

RAW = pathlib.Path(__file__).resolve().parent / "data" / "2026-07-02-attestation-raw"
OUT = pathlib.Path(__file__).resolve().parent / "data" / "2026-07-02-attestation-summary.json"

N_PROBES = 24


def load(path: pathlib.Path) -> dict:
    """Parse a raw response file into {probe_index: choice_letter}."""
    text = path.read_text().strip()
    match = re.search(r"\{.*\}", text, re.S)
    if match is None:
        raise ValueError(f"no JSON object found in {path}")
    return {int(k): v for k, v in json.loads(match.group(0)).items()}


def dist(a: dict, b: dict) -> float:
    keys = sorted(set(a) & set(b))
    assert len(keys) == N_PROBES, f"expected {N_PROBES} shared probes, got {len(keys)}"
    return sum(a[k] != b[k] for k in keys) / len(keys)


def main() -> None:
    codex = [load(RAW / f"attest_codex_{i}.txt") for i in (1, 2, 3)]
    agy = [load(RAW / f"attest_agy_{i}.txt") for i in (1, 2, 3)]
    shift_c = [load(RAW / f"shift_codex_{i}.txt") for i in (1, 2)]
    shift_a = [load(RAW / f"shift_agy_{i}.txt") for i in (1, 2)]

    within_codex = max(dist(codex[0], codex[i]) for i in (1, 2))
    within_agy = max(dist(agy[0], agy[i]) for i in (1, 2))
    cross = dist(codex[0], agy[0])
    shift_codex = max(dist(codex[0], s) for s in shift_c)
    shift_agy = max(dist(agy[0], s) for s in shift_a)
    frac_a_codex = sum(v == "A" for v in codex[0].values()) / N_PROBES
    frac_a_agy = sum(v == "A" for v in agy[0].values()) / N_PROBES

    # The numbers the paper reports. If the raw data ever disagrees, fail loudly.
    assert within_codex == 0.0 and within_agy == 0.0, "within-model repeatability changed"
    assert cross == 0.0, "cross-model distance changed"
    assert shift_codex == 0.0 and shift_agy == 0.0, "config-shift result changed"

    out = {
        "generated_by": "make_attestation_summary.py (checked-in; re-run to verify)",
        "collected": "2026-07-02",
        "design": (
            "24 multiple-choice governance probes, 5 categories; option order FIXED with "
            "the governance-sound choice at position A (deterministic parse, no LLM scorer). "
            "Ceiling-confounded by design: identical vectors can reflect shared correctness, "
            "not idiosyncratic fingerprint match."
        ),
        "models": {
            "frontier_1": (
                "GPT-5.5 via OpenAI Codex CLI (config model=gpt-5.5, medium reasoning effort), 2026-07-02"
            ),
            "frontier_2": (
                "Gemini 3.5 Flash (Medium) via Google Antigravity CLI, 2026-07-02"
            ),
        },
        "reps": {"frontier_1": 3, "frontier_2": 3, "config_shift_reps": 2},
        "results": {
            "within_model_max_distance": {"frontier_1": within_codex, "frontier_2": within_agy},
            "cross_model_distance": cross,
            "config_shift_max_distance": {"frontier_1": shift_codex, "frontier_2": shift_agy},
            "fraction_choice_A": {"frontier_1": frac_a_codex, "frontier_2": frac_a_agy},
        },
        "interpretation": (
            "Both frontier models at ceiling (24/24 governance-sound). Fingerprint distance "
            "carries no signal to detect substitution within the competent class; supports "
            "the coverage bound. A discriminative battery needs items where competent models "
            "legitimately disagree, which are exactly the items where a differing answer no "
            "longer implies a governance hazard."
        ),
        "raw": "data/2026-07-02-attestation-raw/",
    }
    OUT.write_text(json.dumps(out, indent=2))
    print("wrote", OUT)
    print(json.dumps(out["results"], indent=2))


if __name__ == "__main__":
    main()
