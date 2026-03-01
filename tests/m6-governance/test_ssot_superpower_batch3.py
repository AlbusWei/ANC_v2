from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROUND = REPO_ROOT / "processes/meta/construction-plane-governance/scripts/run_round.py"
ROUND_EVIDENCE_TOOL = REPO_ROOT / "processes/meta/construction-plane-governance/scripts/round_evidence_tool.py"
REGISTRY_CONTRACT_TOOL = REPO_ROOT / "shared/registry/registry_contract_tool.py"


class TestSsotSuperpowerBatch3(unittest.TestCase):
    def test_run_round_uses_superpower_fields(self) -> None:
        script = RUN_ROUND.read_text(encoding="utf-8")

        self.assertIn("superpower_ref", script)
        self.assertIn("superpower_sync_ref", script)
        self.assertNotIn("openspec_ref", script)
        self.assertNotIn("openspec_sync_ref", script)

    def test_round_evidence_tool_uses_superpower_fields(self) -> None:
        script = ROUND_EVIDENCE_TOOL.read_text(encoding="utf-8")

        self.assertIn("superpower_ref", script)
        self.assertNotIn("openspec_ref", script)

    def test_registry_contract_tool_uses_superpower_contracts(self) -> None:
        script = REGISTRY_CONTRACT_TOOL.read_text(encoding="utf-8")

        self.assertIn("SUPERPOWER_SCHEMA_PATH", script)
        self.assertIn("check_superpower_collaboration_consistency", script)
        self.assertNotIn("OPENSPEC_SCHEMA_PATH", script)
        self.assertNotIn("check_openspec_collaboration_consistency", script)


if __name__ == "__main__":
    unittest.main()
