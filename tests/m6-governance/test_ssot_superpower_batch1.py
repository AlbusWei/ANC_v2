from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_REGISTRY = REPO_ROOT / "shared/registry/skill_registry.json"
RUN_ROUND = REPO_ROOT / "processes/meta/construction-plane-governance/scripts/run_round.py"


class TestSsotSuperpowerBatch1(unittest.TestCase):
    def test_skill_registry_uses_superpower_sync_as_mainline_entry(self) -> None:
        payload = json.loads(SKILL_REGISTRY.read_text(encoding="utf-8"))
        entries = payload["entries"]
        by_id = {entry["skill_id"]: entry for entry in entries}

        self.assertIn("system.integration.superpower-sync", by_id)
        self.assertNotIn("system.integration.openspec-sync", by_id)

        entry = by_id["system.integration.superpower-sync"]
        self.assertEqual("superpower-sync", entry["name"])
        self.assertEqual("skills/system/superpower-sync/SKILL.md", entry["path"])
        self.assertEqual("skills/system/superpower-sync", entry["openclaw"]["source"])
        self.assertEqual(
            "skills/system/superpower-sync/TEST.md",
            entry["tests"]["test_doc"],
        )

    def test_run_round_invokes_superpower_sync_script(self) -> None:
        script = RUN_ROUND.read_text(encoding="utf-8")

        self.assertIn("skills/system/superpower-sync/scripts/superpower_sync.sh", script)
        self.assertNotIn("skills/system/openspec-sync/scripts/openspec_sync.sh", script)


if __name__ == "__main__":
    unittest.main()
