from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
M1_OPENJUDGE_SPEC = REPO_ROOT / "docs/design/modules/M1-openjudge-adapter-spec.md"
M1_TEST_SYSTEM = REPO_ROOT / "docs/design/modules/M1-test-system.md"
QUALITY_GATE_SKILLS = REPO_ROOT / "docs/design/skills/quality-gate-skills.md"
SELF_DEV_SKILLS = REPO_ROOT / "docs/design/skills/self-development-skills.md"
QUALITY_GATE_RUNNER = REPO_ROOT / "processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py"
M1_REGRESSION = REPO_ROOT / "tests/m1-runtime/run_post_dev_regression.py"


class TestSsotSuperpowerBatch2(unittest.TestCase):
    def test_sdd_tdd_docs_bind_to_superpower_ref(self) -> None:
        docs = {
            "M1-openjudge-adapter-spec": M1_OPENJUDGE_SPEC.read_text(encoding="utf-8"),
            "M1-test-system": M1_TEST_SYSTEM.read_text(encoding="utf-8"),
            "quality-gate-skills": QUALITY_GATE_SKILLS.read_text(encoding="utf-8"),
            "self-development-skills": SELF_DEV_SKILLS.read_text(encoding="utf-8"),
        }

        for name, content in docs.items():
            self.assertIn("superpower_ref", content, f"{name} must include superpower_ref")
            self.assertNotIn("openspec_ref", content.lower(), f"{name} must not include openspec_ref")

    def test_quality_gate_runner_requires_reachable_superpower_ref(self) -> None:
        script = QUALITY_GATE_RUNNER.read_text(encoding="utf-8")

        self.assertIn('required = ["preparation_bundle_ref", "actual_output_refs", "superpower_ref"]', script)
        self.assertIn('raise QualityGateEvaluationError("superpower_ref_unreachable")', script)

    def test_m1_runtime_regression_contains_missing_superpower_ref_fail_closed_case(self) -> None:
        script = M1_REGRESSION.read_text(encoding="utf-8")

        self.assertIn("TC-M1-CHAIN-006", script)
        self.assertIn("missing_superpower_ref", script)
        self.assertIn("superpower_ref_unreachable", script)


if __name__ == "__main__":
    unittest.main()
