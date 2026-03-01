from __future__ import annotations

import json
import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py"


spec = spec_from_file_location("quality_gate_evaluation_runner", RUNNER_PATH)
module = module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


verify_gate_evidence_chain = module.verify_gate_evidence_chain


class GateEvidenceVerifierTests(unittest.TestCase):
    def test_gate_fails_without_openclaw_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            payload = {
                "dispatch_trace_ref": "",
                "phase_outputs": ["tmp/runtime_data/evidence/p1.json"],
                "case_report_ref": "tmp/runtime_data/evidence/case_report.json",
            }

            ok, reason = verify_gate_evidence_chain(payload, repo_root=tmp_path)

            self.assertFalse(ok)
            self.assertEqual(reason, "missing_openclaw_trace")

    def test_gate_fails_when_phase_output_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            dispatch_trace = tmp_path / "tmp/runtime_data/evidence/dispatch.json"
            dispatch_trace.parent.mkdir(parents=True, exist_ok=True)
            dispatch_trace.write_text(json.dumps({"command": "openclaw agent", "return_code": 0}), encoding="utf-8")

            case_report = tmp_path / "tmp/runtime_data/evidence/case_report.json"
            case_report.write_text(
                json.dumps(
                    {
                        "assertions": {
                            "failure_path": True,
                            "rollback_path": True,
                        }
                    }
                ),
                encoding="utf-8",
            )

            payload = {
                "dispatch_trace_ref": "tmp/runtime_data/evidence/dispatch.json",
                "phase_outputs": ["tmp/runtime_data/evidence/missing_p2.json"],
                "case_report_ref": "tmp/runtime_data/evidence/case_report.json",
            }

            ok, reason = verify_gate_evidence_chain(payload, repo_root=tmp_path)

            self.assertFalse(ok)
            self.assertEqual(reason, "missing_phase_output")

    def test_gate_fails_when_case_report_not_representative(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            dispatch_trace = tmp_path / "tmp/runtime_data/evidence/dispatch.json"
            dispatch_trace.parent.mkdir(parents=True, exist_ok=True)
            dispatch_trace.write_text(json.dumps({"command": "openclaw agent", "return_code": 0}), encoding="utf-8")

            phase_output = tmp_path / "tmp/runtime_data/evidence/p1.json"
            phase_output.write_text(json.dumps({"output": "ok"}), encoding="utf-8")

            case_report = tmp_path / "tmp/runtime_data/evidence/case_report.json"
            case_report.write_text(
                json.dumps(
                    {
                        "assertions": {
                            "failure_path": True,
                            "rollback_path": False,
                        }
                    }
                ),
                encoding="utf-8",
            )

            payload = {
                "dispatch_trace_ref": "tmp/runtime_data/evidence/dispatch.json",
                "phase_outputs": ["tmp/runtime_data/evidence/p1.json"],
                "case_report_ref": "tmp/runtime_data/evidence/case_report.json",
            }

            ok, reason = verify_gate_evidence_chain(payload, repo_root=tmp_path)

            self.assertFalse(ok)
            self.assertEqual(reason, "case_report_not_representative")


if __name__ == "__main__":
    unittest.main()
