"""Numerical-contract boundary tests; no model, network or mutation of inputs."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import tempfile
import unittest
import zipfile

from run_offline import CONTROL_SD_PATHS, COST_SD_PATHS, compare_contract, leaf


class ContractBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        archive = Path(__file__).resolve().parents[1] / "inputs" / "research-data.zip"
        with zipfile.ZipFile(archive) as package:
            cls.controls = json.loads(package.read("PFinale-V25-offline/expected-additional/controls.json"))
            cls.costs = json.loads(package.read("PFinale-V25-offline/data/behavior-cost/expected/recorded-cost-results.json"))

    def check(self, actual: dict, expected: dict, contract: str) -> dict:
        with tempfile.TemporaryDirectory(prefix="pf38-contract-") as folder:
            root = Path(folder)
            (root / "actual.json").write_text(json.dumps(actual))
            (root / "expected.json").write_text(json.dumps(expected))
            return compare_contract(root / "actual.json", root / "expected.json", contract)

    @staticmethod
    def assign(document: dict, path: tuple, value: object) -> None:
        branch = document
        for key in path[:-1]:
            branch = branch[key]
        branch[path[-1]] = value

    def test_exact_outputs_and_all_contract_leaves(self):
        self.assertEqual(len(CONTROL_SD_PATHS), 8)
        self.assertEqual(len(COST_SD_PATHS), 12)
        self.assertEqual(self.check(self.controls, self.controls, "controls-eight")["differences"], [])
        self.assertEqual(self.check(self.costs, self.costs, "cost-twelve")["differences"], [])

    def test_only_the_second_allowed_control_value_passes(self):
        changed = copy.deepcopy(self.controls)
        for path in CONTROL_SD_PATHS:
            self.assign(changed, path, 0.37796447300922725)
        result = self.check(changed, self.controls, "controls-eight")
        self.assertEqual(len(result["differences"]), 8)
        self.assign(changed, sorted(CONTROL_SD_PATHS)[0], math.nextafter(0.37796447300922725, math.inf))
        with self.assertRaises(ValueError):
            self.check(changed, self.controls, "controls-eight")

    def test_control_expected_value_is_not_rewritten(self):
        changed = copy.deepcopy(self.controls)
        self.assign(changed, sorted(CONTROL_SD_PATHS)[0], 0.37796447300922725)
        with self.assertRaisesRegex(ValueError, "expected SD"):
            self.check(self.controls, changed, "controls-eight")

    def test_control_variance_requirement_is_exact(self):
        changed = copy.deepcopy(self.controls)
        changed["controls"]["mistral7b"]["task_means"]["0"]["wrong_domain"] = math.nextafter(0.0, 1.0)
        with self.assertRaisesRegex(ValueError, "variance"):
            self.check(changed, self.controls, "controls-eight")

    def test_nonwhitelisted_measurement_change_is_rejected(self):
        changed = copy.deepcopy(self.controls)
        value = changed["controls"]["mistral7b"]["means"]["none"]
        changed["controls"]["mistral7b"]["means"]["none"] = math.nextafter(value, math.inf)
        with self.assertRaisesRegex(ValueError, "non-whitelisted"):
            self.check(changed, self.controls, "controls-eight")

    def test_type_schema_and_missing_field_changes_are_rejected(self):
        for field, value in (("task_count", True), ("application_rows", "35")):
            changed = copy.deepcopy(self.controls)
            changed["controls"]["mistral7b"][field] = value
            with self.assertRaisesRegex(ValueError, "type"):
                self.check(changed, self.controls, "controls-eight")
        changed = copy.deepcopy(self.costs)
        del changed["summary"]["fields"]["evaluator_elapsed_seconds"]["sample_sd"]
        with self.assertRaises(ValueError):
            self.check(changed, self.costs, "cost-twelve")

    def test_cost_tolerance_stays_at_the_original_twelve_fields(self):
        path = ("summary", "fields", "evaluator_elapsed_seconds", "sample_sd")
        value = leaf(self.costs, path)
        limit = max(1e-15, 1e-12 * abs(value))
        changed = copy.deepcopy(self.costs)
        self.assign(changed, path, value + limit / 4)
        self.assertEqual(len(self.check(changed, self.costs, "cost-twelve")["differences"]), 1)
        self.assign(changed, path, value + limit * 4)
        with self.assertRaisesRegex(ValueError, "outside original tolerance"):
            self.check(changed, self.costs, "cost-twelve")
        self.assign(changed, path, float("nan"))
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            self.check(changed, self.costs, "cost-twelve")


if __name__ == "__main__":
    unittest.main()
