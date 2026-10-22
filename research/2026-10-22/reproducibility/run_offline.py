"""Recompute the supported saved-record analyses from the research derivative; never collects responses."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
from fractions import Fraction
import stat
import struct
import subprocess
import sys
import zipfile


ARCHIVE_SHA = "81ce86f32c91d1be8d1c3e0475a24467df986070c0a5b2d7b63dcaec003e63e8"
OUTER_ROOT = "PFinale-V25-offline"
CONTROL_SD_PATHS = {
    tuple(p.split(".")) for p in (
        "controls.mistral7b.task_sd.wrong_domain",
        "controls.qwen7b.contrasts.wrong_domain_minus_none.task_sd",
        "controls.qwen7b.contrasts.hand_minus_none.task_sd",
        "controls.mistral7b_sw.task_sd.none",
        "controls.mistral7b_sw.task_sd.shuffled",
        "controls.mistral7b_sw.task_sd.wrong_domain",
        "controls.mistral7b_sw.contrasts.induced_minus_none.task_sd",
        "controls.mistral7b_sw.contrasts.shuffled_minus_induced.task_sd",
    )
}
COST_SD_PATHS = {
    tuple(p.split(".")) for p in (
        "summary.fields.evaluator_elapsed_seconds.sample_sd",
        "tasks.hiding_Easter_eggs.fields.evaluator_elapsed_seconds.sample_sd",
        "tasks.moving_boxes_to_storage.fields.gate_calls.sample_sd",
        "tasks.assembling_gift_baskets.fields.gate_seconds.sample_sd",
        "tasks.assembling_gift_baskets.fields.evaluator_user_cpu_seconds.sample_sd",
        "tasks.assembling_gift_baskets.fields.evaluator_system_cpu_seconds.sample_sd",
        "tasks.loading_the_car.fields.audit_record_write_seconds.sample_sd",
        "tasks.carrying_in_groceries.fields.evaluator_elapsed_seconds.sample_sd",
        "tasks.clearing_food_from_table_into_fridge.fields.evaluator_elapsed_seconds.sample_sd",
        "tasks.clearing_food_from_table_into_fridge.fields.evaluator_system_cpu_seconds.sample_sd",
        "tasks.rearranging_kitchen_furniture.fields.audit_record_write_seconds.sample_sd",
        "tasks.can_meat.fields.audit_stream_finalize_seconds.sample_sd",
    )
}
CHILD_BOOTSTRAP = r'''
import runpy, sys
from pathlib import Path
sys.dont_write_bytecode = True
def offline_guard(event, args):
    if event.startswith("socket.") or event in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"):
        raise PermissionError("offline reader forbids network or child processes: " + event)
sys.addaudithook(offline_guard)
script = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(script.parent))
sys.argv = sys.argv[1:]
runpy.run_path(str(script), run_name="__main__")
'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_checked(raw: bytes, destination: Path) -> None:
    """Extract fixed archives only after rejecting unsafe/duplicate members."""
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate ZIP member")
        normalized: set[tuple[str, ...]] = set()
        for member in archive.infolist():
            name = member.filename
            parts = PurePosixPath(name).parts
            if (not parts or name.startswith("/") or "\\" in name
                    or any(p in ("", ".", "..") for p in name.rstrip("/").split("/"))
                    or stat.S_ISLNK(member.external_attr >> 16)):
                raise ValueError("unsafe ZIP member: " + name)
            if parts in normalized:
                raise ValueError("duplicate normalized ZIP member")
            normalized.add(parts)
        destination.mkdir()
        archive.extractall(destination)


def run_reader(script: Path, *args: Path | str, cwd: Path | None = None) -> None:
    subprocess.run(
        [sys.executable, "-I", "-B", "-c", CHILD_BOOTSTRAP, str(script), *map(str, args)],
        cwd=cwd or script.parent, check=True, timeout=180,
    )


def exact(actual: Path, expected: Path) -> dict[str, str]:
    if actual.read_bytes() != expected.read_bytes():
        raise ValueError(f"output mismatch: {actual} versus {expected}")
    return {"actual": str(actual), "expected": str(expected), "sha256": sha(actual)}


def leaf(value: dict, path: tuple[str, ...]) -> object:
    for key in path:
        value = value[key]
    return value


def control_vector(document: dict, path: tuple[str, ...]) -> list:
    branch = document["controls"][path[1]]
    if path[2] == "task_sd":
        return [branch["task_means"][key][path[3]] for key in sorted(branch["task_means"])]
    return branch["contrasts"][path[3]]["task_differences"]


def compare_contract(actual: Path, expected: Path, contract: str) -> dict:
    """Apply only the already approved eight/twelve-leaf numerical contracts."""
    observed = json.loads(actual.read_text())
    reference = json.loads(expected.read_text())
    allowed = CONTROL_SD_PATHS if contract == "controls-eight" else COST_SD_PATHS
    if contract not in ("controls-eight", "cost-twelve"):
        raise ValueError("unsupported numerical contract")
    if contract == "controls-eight":
        for path in CONTROL_SD_PATHS:
            a, b = leaf(observed, path), leaf(reference, path)
            if type(b) is not float or b != 0.3779644730092272:
                raise ValueError("controls expected SD drift")
            if type(a) is not float or a not in (0.3779644730092272, 0.37796447300922725):
                raise ValueError("controls SD outside its two-value set")
            for document in (observed, reference):
                raw_vector = control_vector(document, path)
                if len(raw_vector) != 7 or any(type(v) not in (int, float) or not math.isfinite(v) for v in raw_vector):
                    raise ValueError("controls requires seven finite task values")
                vector = [Fraction(v) for v in raw_vector]
                variance = (sum(v*v for v in vector) - sum(vector)**2 / 7) / 6
                if variance != Fraction(1, 7):
                    raise ValueError("controls exact rational variance is not 1/7")
    differences = []
    visited = set()

    def compare(a: object, b: object, path: tuple = ()) -> None:
        if type(a) is not type(b):
            raise ValueError("output type differs at " + repr(path))
        if isinstance(b, dict):
            if set(a) != set(b):
                raise ValueError("output keys differ at " + repr(path))
            for key in b:
                compare(a[key], b[key], path + (key,))
        elif isinstance(b, list):
            if len(a) != len(b):
                raise ValueError("output length differs at " + repr(path))
            for index, (av, bv) in enumerate(zip(a, b)):
                compare(av, bv, path + (index,))
        elif isinstance(b, float):
            if not (math.isfinite(a) and math.isfinite(b)):
                raise ValueError("nonfinite output at " + repr(path))
            if path in allowed:
                visited.add(path)
                if contract == "cost-twelve" and abs(a-b) > max(1e-15, 1e-12 * max(abs(a), abs(b))):
                    raise ValueError("cost SD outside original tolerance")
            if struct.pack("!d", a) != struct.pack("!d", b):
                if path not in allowed:
                    raise ValueError("non-whitelisted float differs at " + repr(path))
                differences.append({"path": "." + ".".join(path), "actual": a, "expected": b})
        elif a != b:
            raise ValueError("output value differs at " + repr(path))

    compare(observed, reference)
    if visited != allowed:
        raise ValueError("numerical contract leaves missing or of wrong type")
    return {"actual": str(actual), "expected": str(expected), "contract": contract,
            "actual_sha256": sha(actual), "expected_sha256": sha(expected),
            "byte_exact": actual.read_bytes() == expected.read_bytes(),
            "allowed_leaf_count": len(allowed), "differences": differences,
            "all_other_output_types_keys_lengths_and_leaves_exact": True}


def reproduce(output: Path, bundle: Path) -> None:
    bundle = bundle.resolve()
    output = output.resolve()
    if output.exists():
        raise ValueError("choose a new output directory; existing paths are never overwritten")
    if output == bundle or bundle in output.parents:
        raise ValueError("output must be outside the immutable bundle")
    source = bundle / "inputs" / "research-data.zip"
    if sha(source) != ARCHIVE_SHA:
        raise ValueError("research derivative archive identity mismatch")
    output.mkdir()
    extract_checked(source.read_bytes(), output / "original")
    outer = output / "original" / OUTER_ROOT
    archives = outer / "data" / "archives"
    extract_checked((archives / "PFinale-V18-prospective-offline-internal-20261019.zip").read_bytes(), output / "pilot-input")
    extract_checked((archives / "PFinale-V22-verified-rule-offline-internal-20261019.zip").read_bytes(), output / "control-input")
    extract_checked((archives / "PFinale-V17-retained-records-candidate-20261019.zip").read_bytes(), output / "retained-input")
    pilot = output / "pilot-input" / "PFinale-prospective-offline"
    control = output / "control-input" / "PFinale-verified-rule-control-offline"
    run_reader(pilot / "portable_report.py", pilot, output / "pilot")
    run_reader(control / "portable_report.py", control, output / "control")
    stage = outer / "data" / "stage"
    run_reader(stage / "recompute.py", pilot, stage / "literal-rule-annotations.json", output / "literal-ledger")
    blind = outer / "cross-family-rule-coding"
    run_reader(stage / "recompute.py", pilot, blind / "gemini-literal-rule-annotations.json", output / "second-ledger")
    run_reader(bundle / "analysis" / "observation_analysis.py", source, output / "observation-classes")
    retained = output / "retained-input" / "retained-records"
    controls = retained / "controls-and-feedback"
    frontier = retained / "frontier-and-attestation"
    retained_out = output / "retained-results"
    retained_out.mkdir()
    run_reader(controls / "analysis" / "controls_recompute.py", "--manifest", "manifests/controls.json", "--output", retained_out / "controls.json", cwd=controls)
    run_reader(controls / "analysis" / "feedback_recompute.py", "--manifest", "manifests/feedback.json", "--output", retained_out / "feedback.json", cwd=controls)
    run_reader(frontier / "analysis" / "recompute.py", "--manifest", "input-manifest.json", "--output", retained_out / "frontier.json", cwd=frontier)
    run_reader(retained / "diagnostic_map.py", "--data-root", controls / "data", "--output", retained_out / "diagnostic.json")
    behavior = outer / "data" / "behavior-cost"
    run_reader(behavior / "analyze.py", cwd=behavior)
    comparisons = [
        exact(output / "pilot" / "analysis.json", outer / "expected-additional" / "pilot-analysis.json"),
        exact(output / "pilot" / "cells.csv", outer / "expected-additional" / "pilot-cells.csv"),
        exact(output / "pilot" / "costs.json", outer / "expected-additional" / "pilot-costs.json"),
        exact(output / "literal-ledger" / "analysis.json", stage / "expected" / "analysis.json"),
        exact(output / "second-ledger" / "analysis.json", blind / "unchanged-reader-output" / "analysis.json"),
        exact(output / "observation-classes" / "analysis.json", bundle / "analysis-output-final" / "analysis.json"),
    ]
    for name in ("analysis.json", "cells.csv", "costs.json", "report.md"):
        comparisons.append(exact(output / "control" / name, control / "expected" / name))
    for name in ("feedback.json", "frontier.json", "diagnostic.json"):
        comparisons.append(exact(retained_out / name, outer / "expected-additional" / name))
    numerical = [
        compare_contract(retained_out / "controls.json", outer / "expected-additional" / "controls.json", "controls-eight"),
        compare_contract(behavior / "recorded-cost-results.json", behavior / "expected" / "recorded-cost-results.json", "cost-twelve"),
    ]
    receipt = {
        "status": "passed", "scope": "Frozen-record recomputation only; not independent model execution, human annotation, scientific acceptance, or public availability.",
        "python": sys.version, "bundle": str(bundle), "output": str(output),
        "archive_sha256": ARCHIVE_SHA, "wrapper_sha256": sha(Path(__file__)),
        "reader_runs": 10, "exact_output_comparisons": comparisons,
        "explicit_numerical_contract_comparisons": numerical,
        "child_guards": "Python audit hooks reject socket operations and child processes; no collector is invoked.",
        "not_run": ["original model execution", "BEHAVIOR simulator/deployment", "missing runtime or substitution-probe implementations", "unavailable all-figure inputs"],
        "rights": "Internal candidate only; inherited rights/path-disclosure conditions remain unresolved.",
    }
    (output / "RECOMPUTATION-RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "passed", "reader_runs": 10, "exact_outputs": len(comparisons), "numerical_contracts": numerical, "receipt": str(output / "RECOMPUTATION-RECEIPT.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new directory outside the immutable candidate")
    options = parser.parse_args()
    reproduce(options.output, Path(__file__).resolve().parents[1])
