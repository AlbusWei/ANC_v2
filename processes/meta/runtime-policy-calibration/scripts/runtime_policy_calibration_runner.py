#!/usr/bin/env python3
"""Executable runner for runtime-policy-calibration process."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class RuntimePolicyCalibrationError(RuntimeError):
    """Fail-closed runtime error for runtime-policy-calibration."""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimePolicyCalibrationError("not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimePolicyCalibrationError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimePolicyCalibrationError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimePolicyCalibrationError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_cmd(cmd: List[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(root), check=False, capture_output=True, text=True)


def parse_last_json(stdout: str) -> Dict[str, Any]:
    for line in reversed([item.strip() for item in stdout.splitlines() if item.strip()]):
        if line.startswith("{") and line.endswith("}"):
            payload = json.loads(line)
            if isinstance(payload, dict):
                return payload
    return {}


def fail_closed(
    *,
    root: Path,
    output_path: Path,
    runtime_trace_path: Path,
    fail_record_path: Path,
    phase_trace: List[Dict[str, Any]],
    reason: str,
) -> int:
    dump_json(
        fail_record_path,
        {
            "timestamp": now_iso(),
            "status": "failed",
            "reason": reason,
            "fail_closed": True,
        },
    )

    dump_json(
        runtime_trace_path,
        {
            "timestamp": now_iso(),
            "process_id": "runtime-policy-calibration",
            "status": "failed",
            "phase_trace": phase_trace,
            "fail_closed_record_ref": to_rel(fail_record_path, root),
            "reason": reason,
        },
    )

    dump_json(
        output_path,
        {
            "status": "failed",
            "process_id": "runtime-policy-calibration",
            "failure_code": "runtime_policy_calibration_failed",
            "reason": reason,
            "runtime_trace_ref": to_rel(runtime_trace_path, root),
            "fail_closed_record_ref": to_rel(fail_record_path, root),
            "calibration_report_ref": "",
            "policy_change_proposal_ref": "",
            "governance_sync_minutes_ref": "",
            "decision_record_ref": "",
            "rollout_observation_ref": "",
        },
    )
    print(to_rel(output_path, root))
    return 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run runtime-policy-calibration process")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--evidence-dir",
        default="",
        help="Evidence directory path (repo-relative). Default runtime_data/execution/evidence/bpm-runtime/w5_runtime_policy_cases/<run_id>",
    )
    parser.add_argument("--run-id", default="", help="Optional run id for evidence directory naming")
    parser.add_argument(
        "--digest-runner",
        default="skills/system/system-feedback-digest/scripts/system_feedback_digest_runner.py",
        help="Repo-relative digest runner path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    request = load_json(input_path)

    run_id = args.run_id.strip() or datetime.now(timezone.utc).strftime("rpc-%Y%m%dT%H%M%SZ")
    evidence_dir = resolve_path(
        root,
        args.evidence_dir.strip() or f"runtime_data/execution/evidence/bpm-runtime/w5_runtime_policy_cases/{run_id}",
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    runtime_trace_path = evidence_dir / "runtime_trace.json"
    fail_record_path = evidence_dir / "fail_closed_record.json"
    phase_trace: List[Dict[str, Any]] = []

    required = ["issue_ref", "runtime_evidence_refs", "current_policy_ref", "risk_constraints_ref", "handoff_ref"]
    missing = [field for field in required if field not in request]
    if missing:
        return fail_closed(
            root=root,
            output_path=output_path,
            runtime_trace_path=runtime_trace_path,
            fail_record_path=fail_record_path,
            phase_trace=phase_trace,
            reason=f"missing required input fields: {','.join(missing)}",
        )

    try:
        issue_ref = str(request["issue_ref"])
        current_policy_ref = str(request["current_policy_ref"])
        risk_constraints_ref = str(request["risk_constraints_ref"])
        handoff_ref = str(request["handoff_ref"])

        issue_path = resolve_path(root, issue_ref)
        policy_path = resolve_path(root, current_policy_ref)
        constraints_path = resolve_path(root, risk_constraints_ref)
        handoff_path = resolve_path(root, handoff_ref)

        for candidate in [issue_path, policy_path, constraints_path, handoff_path]:
            if not candidate.exists():
                raise RuntimePolicyCalibrationError(f"unreachable input ref: {candidate}")

        runtime_evidence_refs_raw = request.get("runtime_evidence_refs")
        if not isinstance(runtime_evidence_refs_raw, list) or not runtime_evidence_refs_raw:
            raise RuntimePolicyCalibrationError("runtime_evidence_refs must be non-empty array")

        runtime_evidence_refs: List[str] = []
        for item in runtime_evidence_refs_raw:
            ref = str(item or "").strip()
            if not ref:
                continue
            if not resolve_path(root, ref).exists():
                raise RuntimePolicyCalibrationError(f"runtime evidence unreachable: {ref}")
            runtime_evidence_refs.append(ref)
        if not runtime_evidence_refs:
            raise RuntimePolicyCalibrationError("runtime_evidence_refs has no reachable entries")

        issue_payload = load_json(issue_path)
        p1_scope_lock = evidence_dir / "p1_scope_lock.json"
        dump_json(
            p1_scope_lock,
            {
                "timestamp": now_iso(),
                "issue_ref": issue_ref,
                "issue_id": issue_payload.get("issue_id", "unknown-issue"),
                "scope": issue_payload.get("scope", "runtime-policy"),
                "objective_ref": issue_payload.get("objective_ref", "obj-runtime-policy-calibration"),
                "locked": True,
            },
        )
        phase_trace.append(
            {
                "phase": "p1-issue-intake-and-scope-lock",
                "status": "pass",
                "scope_lock_ref": to_rel(p1_scope_lock, root),
                "ts": now_iso(),
            }
        )

        p2_evidence_index = evidence_dir / "p2_evidence_index.json"
        dump_json(
            p2_evidence_index,
            {
                "timestamp": now_iso(),
                "refs": runtime_evidence_refs,
                "sample_count": len(runtime_evidence_refs),
                "baseline": {
                    "window": "rolling",
                    "source_count": len(runtime_evidence_refs),
                },
            },
        )
        phase_trace.append(
            {
                "phase": "p2-evidence-collection-and-baseline",
                "status": "pass",
                "evidence_index_ref": to_rel(p2_evidence_index, root),
                "ts": now_iso(),
            }
        )

        digest_runner = resolve_path(root, args.digest_runner)
        if not digest_runner.exists():
            raise RuntimePolicyCalibrationError(f"digest runner not found: {digest_runner}")

        p3_handoff = evidence_dir / "p3_handoff.json"
        handoff_payload = load_json(handoff_path)
        handoff_payload["evidence_ref"] = to_rel(p2_evidence_index, root)
        dump_json(p3_handoff, handoff_payload)

        p3_input = evidence_dir / "p3_digest_input.json"
        p3_output = evidence_dir / "p3_digest_output.json"
        p3_digest = evidence_dir / "p3_analysis_digest.json"
        p3_reject = evidence_dir / "p3_reject.json"
        dump_json(
            p3_input,
            {
                "handoff_ref": to_rel(p3_handoff, root),
                "analysis_scope": "runtime-policy-calibration",
                "max_findings": 5,
            },
        )

        p3_cmd = [
            sys.executable,
            str(digest_runner),
            "--input",
            to_rel(p3_input, root),
            "--output",
            to_rel(p3_output, root),
            "--digest",
            to_rel(p3_digest, root),
            "--reject",
            to_rel(p3_reject, root),
        ]
        p3_proc = run_cmd(p3_cmd, root)
        phase_trace.append(
            {
                "phase": "p3-posterior-analysis-and-hypothesis",
                "status": "pass" if p3_proc.returncode == 0 else "fail",
                "return_code": p3_proc.returncode,
                "stdout": p3_proc.stdout.strip(),
                "stderr": p3_proc.stderr.strip(),
                "digest_output_ref": to_rel(p3_output, root),
                "ts": now_iso(),
            }
        )
        if p3_proc.returncode != 0:
            return fail_closed(
                root=root,
                output_path=output_path,
                runtime_trace_path=runtime_trace_path,
                fail_record_path=fail_record_path,
                phase_trace=phase_trace,
                reason="p3_digest_failed",
            )

        digest_output = load_json(p3_output)
        if digest_output.get("status") != "completed":
            return fail_closed(
                root=root,
                output_path=output_path,
                runtime_trace_path=runtime_trace_path,
                fail_record_path=fail_record_path,
                phase_trace=phase_trace,
                reason="p3_digest_not_completed",
            )

        digest_ref = str(digest_output.get("architecture_feedback_digest_ref") or "")
        if not digest_ref:
            raise RuntimePolicyCalibrationError("missing architecture_feedback_digest_ref")
        digest_payload = load_json(resolve_path(root, digest_ref))

        p4_minutes = evidence_dir / "p4_governance_sync_minutes.json"
        dump_json(
            p4_minutes,
            {
                "timestamp": now_iso(),
                "participants": ["system-analyst", "architect", "admin", "bpm"],
                "digest_ref": digest_ref,
                "conclusion": "进入策略提案与审批阶段",
            },
        )
        phase_trace.append(
            {
                "phase": "p4-governance-sync",
                "status": "pass",
                "governance_sync_minutes_ref": to_rel(p4_minutes, root),
                "ts": now_iso(),
            }
        )

        constraints_payload = load_json(constraints_path)
        require_admin = bool(constraints_payload.get("high_risk_requires_admin_approval", True))
        admin_approved = bool(request.get("admin_approved", False))
        risk_level = str(digest_payload.get("risk_level") or "medium")

        if require_admin and risk_level == "high" and not admin_approved:
            return fail_closed(
                root=root,
                output_path=output_path,
                runtime_trace_path=runtime_trace_path,
                fail_record_path=fail_record_path,
                phase_trace=phase_trace,
                reason="admin_approval_required_for_high_risk_change",
            )

        p5_proposal = evidence_dir / "p5_policy_change_proposal.json"
        dump_json(
            p5_proposal,
            {
                "timestamp": now_iso(),
                "issue_ref": issue_ref,
                "current_policy_ref": current_policy_ref,
                "digest_ref": digest_ref,
                "proposed_actions": digest_payload.get("recommendations", []),
                "rollback_condition": "rollout_observation indicates degradation",
            },
        )

        p5_decision = evidence_dir / "p5_decision_record.json"
        dump_json(
            p5_decision,
            {
                "timestamp": now_iso(),
                "risk_level": risk_level,
                "admin_approved": admin_approved,
                "decision": "approved" if (admin_approved or risk_level != "high") else "blocked",
                "governance_sync_minutes_ref": to_rel(p4_minutes, root),
                "policy_change_proposal_ref": to_rel(p5_proposal, root),
            },
        )
        phase_trace.append(
            {
                "phase": "p5-decision-and-rollout-plan",
                "status": "pass",
                "policy_change_proposal_ref": to_rel(p5_proposal, root),
                "decision_record_ref": to_rel(p5_decision, root),
                "ts": now_iso(),
            }
        )

        p6_observation = evidence_dir / "p6_rollout_observation.json"
        dump_json(
            p6_observation,
            {
                "timestamp": now_iso(),
                "decision_record_ref": to_rel(p5_decision, root),
                "observation_window": "next-1-round",
                "status": "monitoring",
                "notes": "观测窗口已建立，待下一轮采样回灌。",
            },
        )

        calibration_report = evidence_dir / "calibration_report.json"
        dump_json(
            calibration_report,
            {
                "timestamp": now_iso(),
                "issue_ref": issue_ref,
                "digest_ref": digest_ref,
                "policy_change_proposal_ref": to_rel(p5_proposal, root),
                "decision_record_ref": to_rel(p5_decision, root),
                "rollout_observation_ref": to_rel(p6_observation, root),
                "status": "closed",
            },
        )
        phase_trace.append(
            {
                "phase": "p6-post-rollout-observation",
                "status": "pass",
                "rollout_observation_ref": to_rel(p6_observation, root),
                "calibration_report_ref": to_rel(calibration_report, root),
                "ts": now_iso(),
            }
        )

        dump_json(
            runtime_trace_path,
            {
                "timestamp": now_iso(),
                "process_id": "runtime-policy-calibration",
                "status": "ok",
                "phase_trace": phase_trace,
                "input_ref": to_rel(input_path, root),
            },
        )

        output_payload = {
            "status": "ok",
            "process_id": "runtime-policy-calibration",
            "calibration_report_ref": to_rel(calibration_report, root),
            "policy_change_proposal_ref": to_rel(p5_proposal, root),
            "governance_sync_minutes_ref": to_rel(p4_minutes, root),
            "decision_record_ref": to_rel(p5_decision, root),
            "rollout_observation_ref": to_rel(p6_observation, root),
            "architecture_feedback_digest_ref": digest_ref,
            "runtime_trace_ref": to_rel(runtime_trace_path, root),
        }
        dump_json(output_path, output_payload)
        print(to_rel(output_path, root))
        return 0

    except Exception as exc:
        return fail_closed(
            root=root,
            output_path=output_path,
            runtime_trace_path=runtime_trace_path,
            fail_record_path=fail_record_path,
            phase_trace=phase_trace,
            reason=str(exc),
        )


if __name__ == "__main__":
    raise SystemExit(main())
