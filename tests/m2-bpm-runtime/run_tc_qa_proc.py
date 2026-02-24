#!/usr/bin/env python3
"""Run TC-QA-PROC-001~002 for QA process orchestration in M2 W3-B."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("not inside git repository")
    return Path(proc.stdout.strip()).resolve()


def run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_case(cases: List[Dict[str, Any]], case_id: str, ok: bool, details: Dict[str, Any]) -> None:
    cases.append({"id": case_id, "status": "pass" if ok else "fail", "details": details})


def parse_refs(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        items = [item.strip().strip("'\"") for item in text[1:-1].split(",")]
        return [item for item in items if item]
    return [item.strip() for item in text.split(",") if item.strip()]


def prepare_hold_inputs(case_dir: Path, root: Path) -> Dict[str, str]:
    hold_case = case_dir / "hold_case.json"
    runtime_log = case_dir / "runtime.log"
    execution_state = case_dir / "execution_state.json"
    triage_policy = case_dir / "triage_policy.json"
    runtime_health_policy = case_dir / "runtime_health_policy.json"

    dump_json(
        hold_case,
        {
            "case_id": "tc-qa-proc-hold-001",
            "output_heartbeat": True,
            "last_output_heartbeat_at": now_iso(),
        },
    )
    runtime_log.write_text("waiting for subjective review\n", encoding="utf-8")
    dump_json(execution_state, {"phase_progress": "aggregate-gate-decision", "phase_index": 4})
    dump_json(
        triage_policy,
        {
            "allowed_actions": ["continue", "retry", "debug", "fail"],
            "heartbeat_max_age_seconds": 3600,
            "on_no_progress": "debug",
        },
    )
    dump_json(runtime_health_policy, {"max_hold_minutes": 45, "max_retries": 2})

    return {
        "hold_case_ref": str(hold_case.relative_to(root)),
        "runtime_log_ref": str(runtime_log.relative_to(root)),
        "execution_state_ref": str(execution_state.relative_to(root)),
        "triage_policy_ref": str(triage_policy.relative_to(root)),
        "runtime_health_policy_ref": str(runtime_health_policy.relative_to(root)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TC-QA-PROC-001~002")
    parser.add_argument(
        "--preparation-runner",
        default="processes/meta/quality-gate-preparation/scripts/quality_gate_preparation_runner.py",
        help="Repo-relative quality-gate-preparation runner path",
    )
    parser.add_argument(
        "--evaluation-runner",
        default="processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py",
        help="Repo-relative quality-gate-evaluation runner path",
    )
    parser.add_argument(
        "--report",
        default="runtime_data/execution/evidence/bpm-runtime/w3b_tc_qa_proc_report.json",
        help="Repo-relative report output path",
    )
    parser.add_argument(
        "--evidence-root",
        default="runtime_data/execution/evidence/bpm-runtime/w3b_qa_process_cases",
        help="Repo-relative evidence root",
    )
    parser.add_argument(
        "--test-doc-ref",
        default="runtime_data/execution/evidence/quality-gate/runtime-validation-round-2/fixtures/TEST_rule.md",
        help="Repo-relative TEST.md fixture",
    )
    parser.add_argument(
        "--actual-output-ref",
        default="runtime_data/execution/evidence/quality-gate/runtime-validation-round-2/fixtures/actual_output_pass.txt",
        help="Repo-relative actual output fixture",
    )
    parser.add_argument(
        "--profile-set",
        default="quality-gate.baseline@1.0.0",
        help="Comma-separated profile ids",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    prep_runner = (root / args.preparation_runner).resolve()
    eval_runner = (root / args.evaluation_runner).resolve()
    report_path = (root / args.report).resolve()
    evidence_root = (root / args.evidence_root).resolve()

    if not prep_runner.exists():
        raise RuntimeError(f"preparation runner not found: {prep_runner}")
    if not eval_runner.exists():
        raise RuntimeError(f"evaluation runner not found: {eval_runner}")

    test_doc_path = (root / args.test_doc_ref).resolve()
    actual_output_path = (root / args.actual_output_ref).resolve()
    if not test_doc_path.exists():
        raise RuntimeError(f"test doc fixture not found: {test_doc_path}")
    if not actual_output_path.exists():
        raise RuntimeError(f"actual output fixture not found: {actual_output_path}")

    if evidence_root.exists():
        shutil.rmtree(evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=True)

    cases: List[Dict[str, Any]] = []

    # TC-QA-PROC-001: mainline pass
    tc1_dir = evidence_root / "TC-QA-PROC-001"
    tc1_dir.mkdir(parents=True, exist_ok=True)

    tc1_prep_input = tc1_dir / "prep_input.json"
    tc1_prep_output = tc1_dir / "prep_output.json"
    dump_json(
        tc1_prep_input,
        {
            "objective_ref": "obj-m1-unified-quality-gate",
            "spec_ref": "docs/design/modules/M1-openjudge-adapter-spec.md",
            "test_doc_ref": str(test_doc_path.relative_to(root)),
            "risk_focus": ["P0", "P1"],
        },
    )

    tc1_prep_cmd = [
        sys.executable,
        str(prep_runner),
        "--input",
        str(tc1_prep_input),
        "--output",
        str(tc1_prep_output),
        "--evidence-dir",
        str((tc1_dir / "preparation").relative_to(root)),
        "--run-id",
        "TC-QA-PROC-001-prep",
        "--profile-set",
        args.profile_set,
    ]
    tc1_prep_proc = run_cmd(tc1_prep_cmd, root)

    tc1_details: Dict[str, Any] = {
        "prep_return_code": tc1_prep_proc.returncode,
        "prep_stdout": tc1_prep_proc.stdout.strip(),
        "prep_stderr": tc1_prep_proc.stderr.strip(),
    }

    tc1_ok = tc1_prep_proc.returncode == 0 and tc1_prep_output.exists()
    tc1_eval_output_payload: Dict[str, Any] = {}
    if tc1_ok:
        tc1_prep_payload = load_json(tc1_prep_output)
        prep_bundle_ref = str(tc1_prep_payload.get("preparation_bundle_ref") or "")
        prep_verdict = str(tc1_prep_payload.get("verdict") or "")
        tc1_ok = tc1_ok and prep_verdict == "pass" and bool(prep_bundle_ref)
        tc1_details.update(
            {
                "preparation_bundle_ref": prep_bundle_ref,
                "preparation_verdict": prep_verdict,
            }
        )

        tc1_eval_input = tc1_dir / "evaluation_input.json"
        tc1_eval_output = tc1_dir / "evaluation_output.json"
        dump_json(
            tc1_eval_input,
            {
                "preparation_bundle_ref": prep_bundle_ref,
                "actual_output_refs": [str(actual_output_path.relative_to(root))],
                "profile_set": parse_refs(args.profile_set),
                "force_hold": False,
            },
        )

        tc1_eval_cmd = [
            sys.executable,
            str(eval_runner),
            "--input",
            str(tc1_eval_input),
            "--output",
            str(tc1_eval_output),
            "--evidence-dir",
            str((tc1_dir / "evaluation").relative_to(root)),
            "--run-id",
            "TC-QA-PROC-001-eval",
        ]
        tc1_eval_proc = run_cmd(tc1_eval_cmd, root)
        tc1_details.update(
            {
                "eval_return_code": tc1_eval_proc.returncode,
                "eval_stdout": tc1_eval_proc.stdout.strip(),
                "eval_stderr": tc1_eval_proc.stderr.strip(),
            }
        )

        tc1_ok = tc1_ok and tc1_eval_proc.returncode == 0 and tc1_eval_output.exists()
        if tc1_ok:
            tc1_eval_output_payload = load_json(tc1_eval_output)
            gate_decision = str(tc1_eval_output_payload.get("gate_decision") or "")
            hold_routed = bool(tc1_eval_output_payload.get("hold_routed"))
            final_gate_verdict_ref = str(tc1_eval_output_payload.get("final_gate_verdict_ref") or "")
            tc1_ok = tc1_ok and gate_decision == "pass" and (not hold_routed) and bool(final_gate_verdict_ref)
            tc1_details.update(
                {
                    "gate_decision": gate_decision,
                    "hold_routed": hold_routed,
                    "final_gate_verdict_ref": final_gate_verdict_ref,
                }
            )

    append_case(cases, "TC-QA-PROC-001", tc1_ok, tc1_details)

    # TC-QA-PROC-002: hold branch reachable
    tc2_dir = evidence_root / "TC-QA-PROC-002"
    tc2_dir.mkdir(parents=True, exist_ok=True)

    tc2_prep_input = tc2_dir / "prep_input.json"
    tc2_prep_output = tc2_dir / "prep_output.json"
    dump_json(
        tc2_prep_input,
        {
            "objective_ref": "obj-m1-unified-quality-gate",
            "spec_ref": "docs/design/modules/M1-openjudge-adapter-spec.md",
            "test_doc_ref": str(test_doc_path.relative_to(root)),
            "risk_focus": ["P0", "P1"],
        },
    )

    tc2_prep_cmd = [
        sys.executable,
        str(prep_runner),
        "--input",
        str(tc2_prep_input),
        "--output",
        str(tc2_prep_output),
        "--evidence-dir",
        str((tc2_dir / "preparation").relative_to(root)),
        "--run-id",
        "TC-QA-PROC-002-prep",
        "--profile-set",
        args.profile_set,
    ]
    tc2_prep_proc = run_cmd(tc2_prep_cmd, root)

    tc2_details: Dict[str, Any] = {
        "prep_return_code": tc2_prep_proc.returncode,
        "prep_stdout": tc2_prep_proc.stdout.strip(),
        "prep_stderr": tc2_prep_proc.stderr.strip(),
    }

    tc2_ok = tc2_prep_proc.returncode == 0 and tc2_prep_output.exists()
    if tc2_ok:
        tc2_prep_payload = load_json(tc2_prep_output)
        prep_bundle_ref = str(tc2_prep_payload.get("preparation_bundle_ref") or "")
        tc2_ok = tc2_ok and bool(prep_bundle_ref) and str(tc2_prep_payload.get("verdict") or "") == "pass"

        hold_inputs = prepare_hold_inputs(tc2_dir, root)

        tc2_eval_input = tc2_dir / "evaluation_input.json"
        tc2_eval_output = tc2_dir / "evaluation_output.json"
        dump_json(
            tc2_eval_input,
            {
                "preparation_bundle_ref": prep_bundle_ref,
                "actual_output_refs": [str(actual_output_path.relative_to(root))],
                "profile_set": parse_refs(args.profile_set),
                "force_hold": True,
                **hold_inputs,
            },
        )

        tc2_eval_cmd = [
            sys.executable,
            str(eval_runner),
            "--input",
            str(tc2_eval_input),
            "--output",
            str(tc2_eval_output),
            "--evidence-dir",
            str((tc2_dir / "evaluation").relative_to(root)),
            "--run-id",
            "TC-QA-PROC-002-eval",
        ]
        tc2_eval_proc = run_cmd(tc2_eval_cmd, root)

        tc2_details.update(
            {
                "eval_return_code": tc2_eval_proc.returncode,
                "eval_stdout": tc2_eval_proc.stdout.strip(),
                "eval_stderr": tc2_eval_proc.stderr.strip(),
                "preparation_bundle_ref": prep_bundle_ref,
            }
        )

        tc2_ok = tc2_ok and tc2_eval_proc.returncode == 0 and tc2_eval_output.exists()
        if tc2_ok:
            tc2_eval_payload = load_json(tc2_eval_output)
            gate_decision = str(tc2_eval_payload.get("gate_decision") or "")
            hold_routed = bool(tc2_eval_payload.get("hold_routed"))
            hold_governance_output_ref = str(tc2_eval_payload.get("hold_governance_output_ref") or "")
            hold_resolution_ref = str(tc2_eval_payload.get("hold_resolution_ref") or "")

            tc2_ok = (
                tc2_ok
                and gate_decision == "hold"
                and hold_routed
                and bool(hold_governance_output_ref)
                and bool(hold_resolution_ref)
                and (root / hold_governance_output_ref).exists()
                and (root / hold_resolution_ref).exists()
            )
            tc2_details.update(
                {
                    "gate_decision": gate_decision,
                    "hold_routed": hold_routed,
                    "hold_governance_output_ref": hold_governance_output_ref,
                    "hold_resolution_ref": hold_resolution_ref,
                }
            )

    append_case(cases, "TC-QA-PROC-002", tc2_ok, tc2_details)

    passed = sum(1 for case in cases if case["status"] == "pass")
    failed = len(cases) - passed
    report = {
        "ts": now_iso(),
        "suite": "TC-QA-PROC-001~002",
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "evidence_root": args.evidence_root,
        "cases": cases,
    }
    dump_json(report_path, report)

    print(json.dumps(report, ensure_ascii=False))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
