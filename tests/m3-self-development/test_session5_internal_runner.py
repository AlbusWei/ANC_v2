from __future__ import annotations

import json
import sys
import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "tests/m3-self-development/session5_internal_runner.py"

spec = spec_from_file_location("session5_internal_runner", RUNNER_PATH)
module = module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


run_quality_gate_evaluation = module.run_quality_gate_evaluation
run_quality_gate_preparation = module.run_quality_gate_preparation
case_success_payload = module.case_success_payload


class Session5InternalRunnerTests(unittest.TestCase):
    def test_case_success_payload_sets_representative_assertions(self) -> None:
        payload = case_success_payload(
            "M3-INT-001",
            {
                "objective_ref": "obj.json",
                "final_gate_verdict_ref": "gate.json",
                "lifecycle_transition_ref": "life.json",
                "registry_sync_ref": "reg.json",
                "candidate_artifacts_ref": "cand.json",
                "rollback_bundle_ref": "rollback.json",
                "liveness_probes": [],
                "gate_chain_refs": [],
            },
            "ok",
        )

        details = payload.get("details")
        self.assertIsInstance(details, dict)
        self.assertTrue(details.get("failure_path"))
        self.assertTrue(details.get("rollback_path"))

    def test_quality_gate_input_includes_evidence_chain_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            case_dir = root / "tmp/runtime_data/execution/evidence/case-001"
            case_dir.mkdir(parents=True, exist_ok=True)

            prep = case_dir / "quality-gate-preparation/output.json"
            prep.parent.mkdir(parents=True, exist_ok=True)
            prep.write_text("{}", encoding="utf-8")

            impl = case_dir / "implementation-execution-core/implementation_result.json"
            impl.parent.mkdir(parents=True, exist_ok=True)
            impl.write_text("{}", encoding="utf-8")

            dispatch = case_dir / "dispatch/quality-gate-evaluation/dispatch_output.json"
            dispatch.parent.mkdir(parents=True, exist_ok=True)
            dispatch.write_text("{}", encoding="utf-8")

            case_report = case_dir / "case_report.json"
            case_report.write_text(json.dumps({"assertions": {"failure_path": True, "rollback_path": True}}), encoding="utf-8")

            def _fake_run_cmd(_cmd: list[str], _cwd: Path):
                output_path = case_dir / "quality-gate-evaluation/output.json"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(json.dumps({"status": "ok", "gate_decision": "pass"}), encoding="utf-8")

                class _Proc:
                    returncode = 0
                    stdout = ""
                    stderr = ""

                return _Proc()

            with patch.object(module, "run_cmd", side_effect=_fake_run_cmd):
                run_quality_gate_evaluation(
                    root=root,
                    case_dir=case_dir,
                    preparation_bundle_ref=prep.relative_to(root).as_posix(),
                    actual_output_refs=[impl.relative_to(root).as_posix()],
                    superpower_ref="docs/plans/SuperPower.md",
                    dispatch_trace_ref=dispatch.relative_to(root).as_posix(),
                    case_report_ref=case_report.relative_to(root).as_posix(),
                    phase_outputs=[
                        prep.relative_to(root).as_posix(),
                        impl.relative_to(root).as_posix(),
                    ],
                )

            input_path = case_dir / "quality-gate-evaluation/input.json"
            payload = json.loads(input_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("dispatch_trace_ref"), dispatch.relative_to(root).as_posix())
            self.assertEqual(payload.get("case_report_ref"), case_report.relative_to(root).as_posix())
            self.assertEqual(payload.get("superpower_ref"), "docs/plans/SuperPower.md")
            self.assertEqual(
                payload.get("phase_outputs"),
                [prep.relative_to(root).as_posix(), impl.relative_to(root).as_posix()],
            )

    def test_quality_gate_preparation_input_includes_superpower_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            case_dir = root / "tmp/runtime_data/execution/evidence/case-002"
            case_dir.mkdir(parents=True, exist_ok=True)

            test_doc = case_dir / "fixtures/test_doc.md"
            test_doc.parent.mkdir(parents=True, exist_ok=True)
            test_doc.write_text("# test", encoding="utf-8")

            def _fake_run_cmd(_cmd: list[str], _cwd: Path):
                output_path = case_dir / "quality-gate-preparation/output.json"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(
                    json.dumps({"status": "ok", "verdict": "pass", "preparation_bundle_ref": "bundle.json"}),
                    encoding="utf-8",
                )

                class _Proc:
                    returncode = 0
                    stdout = ""
                    stderr = ""

                return _Proc()

            with patch.object(module, "run_cmd", side_effect=_fake_run_cmd):
                run_quality_gate_preparation(
                    root=root,
                    case_dir=case_dir,
                    objective_ref="objective.json",
                    spec_ref="spec.json",
                    test_doc_ref=test_doc.relative_to(root).as_posix(),
                    superpower_ref="docs/plans/SuperPower.md",
                )

            prep_input = case_dir / "quality-gate-preparation/input.json"
            payload = json.loads(prep_input.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("superpower_ref"), "docs/plans/SuperPower.md")


if __name__ == "__main__":
    unittest.main()
