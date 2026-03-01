from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESS_MANIFEST = REPO_ROOT / "processes/meta/construction-plane-governance/process.json"
SKILL_DOC = REPO_ROOT / "processes/meta/construction-plane-governance/SKILL.md"
PROCESS_DOC = REPO_ROOT / "processes/meta/construction-plane-governance/PROCESS.md"


class TestSsotSuperpowerBatch0(unittest.TestCase):
    def test_process_manifest_switches_to_superpower_contract_fields(self) -> None:
        payload = json.loads(PROCESS_MANIFEST.read_text(encoding="utf-8"))

        required_input = payload["input_contract"]["required"]
        required_output = payload["output_contract"]["required"]
        phase4 = next(phase for phase in payload["phases"] if phase["phase_id"] == "p4")

        self.assertIn("superpower_ref", required_input)
        self.assertNotIn("openspec_ref", required_input)
        self.assertIn("superpower_sync_ref", required_output)
        self.assertNotIn("openspec_sync_ref", required_output)
        self.assertEqual("sync-superpower-state", phase4["name"])
        self.assertEqual("system.integration.superpower-sync", phase4["inline_ap"]["skill_id"])

    def test_docs_drop_openspec_terms_for_mainline_contract(self) -> None:
        skill_text = SKILL_DOC.read_text(encoding="utf-8")
        process_text = PROCESS_DOC.read_text(encoding="utf-8")

        for content in (skill_text, process_text):
            lowered = content.lower()
            self.assertNotIn("openspec_ref", lowered)
            self.assertNotIn("openspec_sync_ref", lowered)
            self.assertNotIn("system.integration.openspec-sync", lowered)

        self.assertIn("superpower_ref", skill_text)
        self.assertIn("superpower_sync_ref", skill_text)
        self.assertIn("superpower_ref", process_text)
        self.assertIn("superpower_sync_ref", process_text)


if __name__ == "__main__":
    unittest.main()
