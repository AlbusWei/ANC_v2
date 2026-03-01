from __future__ import annotations

import sys
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "tests/m3-self-development/session6_external_runner.py"

spec = spec_from_file_location("session6_external_runner", RUNNER_PATH)
module = module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


case_pass = module.case_pass


class Session6ExternalRunnerTests(unittest.TestCase):
    def test_case_pass_sets_representative_assertions(self) -> None:
        payload = case_pass(
            "M3-EXT-001",
            "ok",
            details={"objective_ref": "obj.json"},
        )

        details = payload.get("details")
        self.assertIsInstance(details, dict)
        self.assertTrue(details.get("failure_path"))
        self.assertTrue(details.get("rollback_path"))


if __name__ == "__main__":
    unittest.main()
