"""Post-hoc projections of retained rule/choice evidence; offline, no model calls.

The fixed archive and its original semantic annotations are inputs. Byte binding
does not authenticate original execution or turn AI coding into semantic gold.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import io
import json
from pathlib import Path
import zipfile


ARCHIVE_SHA = "81ce86f32c91d1be8d1c3e0475a24467df986070c0a5b2d7b63dcaec003e63e8"
PLAN_SHA = "d3983a0b17ada80df101afcd540962cf0ae80dc6de974c9c2c2bdde63b1b6834"
TERMINAL_SHA = "c5236f99553a553c2631ec2492754edc867300a508cfde0eaa2f286a31ebfa9f"
ARMS = ("direct-reference", "generated-reference", "direct-flipped", "generated-flipped")
OPPOSITE = {"agrees_with_supplied", "contradicts_supplied"}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def load_inputs(archive: Path) -> dict:
    raw = archive.read_bytes()
    require(digest(raw) == ARCHIVE_SHA, "not the fixed offline archive")
    outer_root = "PFinale-V25-offline/"
    with zipfile.ZipFile(io.BytesIO(raw)) as outer:
        require(len(outer.namelist()) == len(set(outer.namelist())), "duplicate outer member")
        annotation_raw = outer.read(outer_root + "data/stage/literal-rule-annotations.json")
        pilot_raw = outer.read(outer_root + "data/archives/PFinale-V18-prospective-offline-internal-20261019.zip")
    root = "PFinale-prospective-offline/"
    with zipfile.ZipFile(io.BytesIO(pilot_raw)) as pilot:
        require(len(pilot.namelist()) == len(set(pilot.namelist())), "duplicate pilot member")
        plan_raw = pilot.read(root + "frozen/plan.json")
        terminal_raw = pilot.read(root + "run/terminal.json")
        require(digest(plan_raw) == PLAN_SHA, "frozen plan changed")
        require(digest(terminal_raw) == TERMINAL_SHA, "terminal changed")
        terminal = json.loads(terminal_raw)
        files = {}
        for binding in terminal["files"]:
            name = binding["path"]
            require(isinstance(name, str) and name not in ("", ".", "..")
                    and Path(name).name == name and "\\" not in name, "invalid record name")
            require(name not in files, "duplicate record binding")
            files[name] = pilot.read(root + "run/" + name)
    return {
        "plan": json.loads(plan_raw), "terminal": terminal,
        "files": files, "annotations": json.loads(annotation_raw),
        "identities": {
            "outer_archive_sha256": digest(raw), "pilot_archive_sha256": digest(pilot_raw),
            "annotations_sha256": digest(annotation_raw),
            "plan_sha256": digest(plan_raw), "terminal_sha256": digest(terminal_raw),
        },
    }


def literal_cells(plan: dict, files: dict, annotations: dict) -> dict:
    expected = {j["id"] for j in plan["jobs"] if j["kind"] == "rule"}
    annotated = set()
    cells = {}
    for rule in annotations["rules"]:
        rid = rule["job"]
        require(rid in expected and rid not in annotated, "unexpected or duplicate annotated rule")
        annotated.add(rid)
        text = json.loads(files[rid + ".wire.json"])["response"]
        require(digest(text.encode()) == rule["raw_text_sha256"], "rule text changed")
        condition = rid.rsplit("-", 1)[-1]
        require(condition in ("reference", "flipped"), "unexpected rule condition")
        for operator in rule["operators"]:
            quotes = operator["quotes"]
            require(quotes and all(isinstance(q, str) and q.strip() and q in text for q in quotes),
                    "unsupported rule quote")
            for cell in operator["cells"]:
                require(type(cell["owned"]) is bool and type(cell["public"]) is bool,
                        "non-Boolean annotated attributes")
                key = (rid, operator["operator"], cell["owned"], cell["public"])
                require(key not in cells, "duplicate annotated cell")
                matched = [r for r in plan["dataset"]["train"]
                           if (r["operator"], r["owned"], r["public"]) == key[1:]]
                require(len(matched) == 1, "annotation outside frozen training domain")
                target = matched[0][condition + "_choice"]
                actions, qualification = cell["action_constraints"], cell["qualification"]
                if qualification == "singleton" and actions in (["admit"], ["defer"]):
                    status = "agrees_with_supplied" if actions[0] == target else "contradicts_supplied"
                elif qualification == "silent" and actions == []:
                    status = "silent"
                elif qualification in ("ambiguous_scope", "conflicting_clauses") and actions == ["admit", "defer"]:
                    status = qualification
                else:
                    raise ValueError("invalid annotation qualification")
                cells[key] = {
                    "literal_status": status, "constraint": actions,
                    "quotes": quotes, "rule_text_sha256": rule["raw_text_sha256"],
                }
    require(annotated == expected and len(cells) == 64, "incomplete eight-rule annotation")
    return cells


def projection(rows: list, fields: tuple) -> dict:
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[f] for f in fields)].append(row)
    result = []
    for key in sorted(groups):
        members = sorted(groups[key], key=lambda r: r["id"])
        statuses = sorted({r["literal_status"] for r in members})
        result.append({
            "observation": dict(zip(fields, key)),
            "statuses": statuses,
            "singleton_opposition": OPPOSITE <= set(statuses),
            "members": members,
        })
    return {
        "fields": list(fields), "classes": len(result),
        "mixed_status_classes": sum(len(r["statuses"]) > 1 for r in result),
        "singleton_opposition_classes": sum(r["singleton_opposition"] for r in result),
        "class_size_distribution": dict(sorted(Counter(len(r["members"]) for r in result).items())),
        "class_records": result,
    }


def analyse(inputs: dict) -> dict:
    plan, terminal, files = inputs["plan"], inputs["terminal"], inputs["files"]
    ids = [j["id"] for j in plan["jobs"]]
    require(len(ids) == len(set(ids)), "duplicate job")
    require(terminal["status"] == "done", "campaign not completed")
    bindings = terminal["files"]
    require(len(bindings) == len({b["path"] for b in bindings}), "duplicate record binding")
    for binding in bindings:
        require(binding["path"] in files
                and digest(files[binding["path"]]) == binding["sha256"], "record hash mismatch")
    require(set(files) == {b["path"] for b in bindings}, "record set mismatch")
    cells = literal_cells(plan, files, inputs["annotations"])
    tests = {t["id"]: t for t in plan["dataset"]["tests"]}
    require(len(tests) == len(plan["dataset"]["tests"]), "duplicate test item")
    all_rows, generated = [], []
    for job in plan["jobs"]:
        if job.get("arm") not in ARMS:
            continue
        require(terminal["states"][job["id"]] == "done", "incomplete decision")
        wire_name = job["id"] + ".wire.json"
        wire = json.loads(files[wire_name])
        choice = json.loads(wire["response"])
        require(isinstance(choice, dict) and set(choice) == {"choice"}
                and choice["choice"] in ("admit", "defer"), "expected a complete binary choice")
        choice = choice["choice"]
        test = job["test"]
        require(test["id"] in tests and test == tests[test["id"]], "test differs from frozen item")
        condition = job["condition"]
        require(condition in ("reference", "flipped"), "invalid decision condition")
        require(test["reference_choice"] in ("admit", "defer")
                and test["flipped_choice"] in ("admit", "defer")
                and test["reference_choice"] != test["flipped_choice"], "targets not complementary")
        supplied = test[condition + "_choice"]
        row = {
            "id": job["id"], "block": job["block"], "arm": job["arm"],
            "condition": condition, "test_id": test["id"], "document": test["document"],
            "operator": test["operator"], "owned": test["owned"], "public": test["public"],
            "choice": choice, "reference_choice": test["reference_choice"],
            "supplied_choice": supplied, "fixed_reference_agreement": choice == test["reference_choice"],
            "supplied_mapping_agreement": choice == supplied,
            "wire_sha256": digest(files[wire_name]),
        }
        all_rows.append(row)
        if job["arm"].startswith("generated-"):
            require(job.get("rule_id") == "rule-" + str(job["block"]) + "-" + condition,
                    "rule-context binding mismatch")
            key = (job["rule_id"], test["operator"], test["owned"], test["public"])
            require(key in cells, "missing literal cell")
            generated.append({**row, "rule": job["rule_id"], **cells[key]})
        else:
            require(not job.get("rule_id"), "direct arm unexpectedly uses generated rule")
    require(len(all_rows) == 128 and len(generated) == 64, "wrong finite decision domain")
    readouts = []
    for arm in (*ARMS, "direct-pooled", "generated-pooled"):
        selected = [r for r in all_rows if r["arm"] == arm] if not arm.endswith("-pooled") else [
            r for r in all_rows if r["arm"].startswith(arm.split("-")[0] + "-")]
        require(len(selected) == (64 if arm.endswith("-pooled") else 32), "incomplete arm")
        readouts.append({
            "arm": arm, "n": len(selected),
            "fixed_reference_agreements": sum(r["fixed_reference_agreement"] for r in selected),
            "supplied_mapping_agreements": sum(r["supplied_mapping_agreement"] for r in selected),
        })
    return {
        "scope": "Exploratory finite observation-class analysis of existing records. Semantic annotations remain explicit AI-assisted inputs; no hidden mechanism, causal intervention, authenticated authority or population estimate.",
        "identities": inputs["identities"],
        "target_readouts": readouts,
        "item_projection": projection(generated, ("condition", "test_id", "choice")),
        "attribute_projection": projection(generated, ("condition", "operator", "owned", "public", "choice")),
        "decisions": sorted(all_rows, key=lambda r: r["id"]),
    }


def run(archive: Path, output: Path) -> None:
    require(not output.exists(), "output already exists")
    result = analyse(load_inputs(archive))
    output.mkdir()
    raw = (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    (output / "analysis.json").write_bytes(raw)
    manifest = {
        "reader_sha256": digest(Path(__file__).read_bytes()),
        "outer_archive_sha256": ARCHIVE_SHA,
        "analysis_sha256": digest(raw),
        "scope": "Offline byte binding and deterministic reanalysis; not authenticated execution.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run(args.archive, args.output)
