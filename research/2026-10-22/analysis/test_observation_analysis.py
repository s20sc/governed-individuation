"""Offline checks of the post-hoc observation analysis; no model or network."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from observation_analysis import analyse, load_inputs


ARCHIVE = Path(__file__).resolve().parents[1] / "inputs" / "research-data.zip"


class ObservationAnalysisChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = load_inputs(ARCHIVE)

    def test_independently_counted_finite_results(self):
        result = analyse(self.inputs)
        self.assertEqual(result["item_projection"]["classes"], 30)
        self.assertEqual(result["item_projection"]["mixed_status_classes"], 11)
        self.assertEqual(result["item_projection"]["singleton_opposition_classes"], 5)
        self.assertEqual(result["attribute_projection"]["classes"], 15)
        self.assertEqual(result["attribute_projection"]["mixed_status_classes"], 6)
        self.assertEqual(result["attribute_projection"]["singleton_opposition_classes"], 3)
        actual = {
            r["arm"]: (r["fixed_reference_agreements"], r["supplied_mapping_agreements"])
            for r in result["target_readouts"]
        }
        self.assertEqual(actual, {
            "direct-reference": (25, 25), "generated-reference": (15, 15),
            "direct-flipped": (12, 20), "generated-flipped": (20, 12),
            "direct-pooled": (37, 45), "generated-pooled": (35, 27),
        })

    def test_input_order_does_not_change_results(self):
        changed = copy.deepcopy(self.inputs)
        changed["plan"]["jobs"].reverse()
        changed["annotations"]["rules"].reverse()
        for rule in changed["annotations"]["rules"]:
            rule["operators"].reverse()
            for operator in rule["operators"]:
                operator["cells"].reverse()
        self.assertEqual(analyse(changed), analyse(self.inputs))

    def test_duplicate_job_is_rejected(self):
        changed = copy.deepcopy(self.inputs)
        changed["plan"]["jobs"].append(copy.deepcopy(changed["plan"]["jobs"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate job"):
            analyse(changed)

    def test_unsupported_quote_is_rejected(self):
        changed = copy.deepcopy(self.inputs)
        changed["annotations"]["rules"][0]["operators"][0]["quotes"] = ["NOT IN THE RETAINED RULE"]
        with self.assertRaisesRegex(ValueError, "quote"):
            analyse(changed)

    def test_invalid_choice_is_rejected_after_updating_record_binding(self):
        changed = copy.deepcopy(self.inputs)
        job = next(j for j in changed["plan"]["jobs"] if j.get("arm") == "direct-reference")
        name = job["id"] + ".wire.json"
        wire = json.loads(changed["files"][name])
        wire["response"] = '{"choice":"maybe"}'
        raw = json.dumps(wire).encode()
        changed["files"][name] = raw
        for binding in changed["terminal"]["files"]:
            if binding["path"] == name:
                binding["sha256"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, "binary choice"):
            analyse(changed)

    def test_empty_or_whitespace_quote_is_rejected(self):
        for quote in ("", "   "):
            with self.subTest(quote=repr(quote)):
                changed = copy.deepcopy(self.inputs)
                changed["annotations"]["rules"][0]["operators"][0]["quotes"] = [quote]
                with self.assertRaisesRegex(ValueError, "quote"):
                    analyse(changed)

    def test_changed_wire_without_new_binding_is_rejected(self):
        changed = copy.deepcopy(self.inputs)
        name = next(n for n in changed["files"] if n.endswith(".wire.json"))
        changed["files"][name] += b"\n"
        with self.assertRaisesRegex(ValueError, "record hash"):
            analyse(changed)


if __name__ == "__main__":
    unittest.main()
