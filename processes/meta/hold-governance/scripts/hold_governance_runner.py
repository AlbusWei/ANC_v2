#!/usr/bin/env python3
"""Executable runner for hold-governance process."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class HoldGovernanceError(RuntimeError):
    """Fail-closed runtime error for hold-governance."""


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
        raise HoldGovernanceError("not inside a git repository")
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
        raise HoldGovernanceError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HoldGovernanceError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise HoldGovernanceError(f"json root must be object: {path}")
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
    raise HoldGovernanceError("runner stdout does not contain json object")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run hold-governance process")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--evidence-dir",
        default="",
        help="Evidence directory path (repo-relative). Default docs/design/modules/evidence/bpm-runtime/w3b_qa_process_cases/<run_id>/hold-governance",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Optional run id for evidence directory naming",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    request = load_json(input_path)

    run_id = args.run_id.strip() or datetime.now(timezone.utc).strftime("hold-governance-%Y%m%dT%H%M%SZ")
    evidence_dir = resolve_path(
        root,
        args.evidence_dir.strip()
        or f"docs/design/modules/evidence/bpm-runtime/w3b_qa_process_cases/{run_id}/hold-governance",
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    runtime_trace_path = evidence_dir / "runtime_trace.json"
    fail_closed_path = evidence_dir / "fail_closed_record.json"

    phase_trace: List[Dict[str, Any]] = []

    try:
        required = [
            "hold_case_ref",
            "runtime_log_ref",
            "execution_state_ref",
            "triage_policy_ref",
            "runtime_health_policy_ref",
        ]
        missing = [key for key in required if key not in request]
        if missing:
            raise HoldGovernanceError(f"missing required input fields: {','.join(missing)}")

        hold_case_ref = to_rel(resolve_path(root, str(request["hold_case_ref"])), root)
        runtime_log_ref = to_rel(resolve_path(root, str(request["runtime_log_ref"])), root)
        execution_state_ref = to_rel(resolve_path(root, str(request["execution_state_ref"])), root)
        triage_policy_ref = to_rel(resolve_path(root, str(request["triage_policy_ref"])), root)
        runtime_health_policy_ref = to_rel(resolve_path(root, str(request["runtime_health_policy_ref"])), root)

        for ref in [hold_case_ref, runtime_log_ref, execution_state_ref, triage_policy_ref, runtime_health_policy_ref]:
            if not resolve_path(root, ref).exists():
                raise HoldGovernanceError(f"required_ref_unreachable:{ref}")

        # p1+p2+p3: hold-triage chain
        p123_dir = evidence_dir / "p1_p3_hold_triage"
        p123_dir.mkdir(parents=True, exist_ok=True)
        triage_cmd = [
            sys.executable,
            "skills/system/qa/hold-triage/scripts/hold_triage.py",
            "--hold-case",
            hold_case_ref,
            "--runtime-log",
            runtime_log_ref,
            "--execution-state",
            execution_state_ref,
            "--triage-policy",
            triage_policy_ref,
            "--output-dir",
            to_rel(p123_dir, root),
        ]
        prev_runtime = str(request.get("previous_runtime_log_ref") or "").strip()
        prev_state = str(request.get("previous_execution_state_ref") or "").strip()
        if prev_runtime:
            prev_runtime_rel = to_rel(resolve_path(root, prev_runtime), root)
            triage_cmd.extend(["--previous-runtime-log", prev_runtime_rel])
        if prev_state:
            prev_state_rel = to_rel(resolve_path(root, prev_state), root)
            triage_cmd.extend(["--previous-execution-state", prev_state_rel])

        triage_proc = run_cmd(triage_cmd, root)
        (p123_dir / "stdout.txt").write_text(triage_proc.stdout, encoding="utf-8")
        (p123_dir / "stderr.txt").write_text(triage_proc.stderr, encoding="utf-8")

        triage_payload = parse_last_json(triage_proc.stdout)
        triage_action = str(triage_payload.get("triage_action") or "fail").strip()
        triage_report_ref = str(triage_payload.get("triage_report_ref") or "")
        action_execution_ref = str(triage_payload.get("action_execution_ref") or "")
        progress_signals_ref = str(triage_payload.get("progress_signals_ref") or "")

        if triage_proc.returncode not in (0, 40):
            raise HoldGovernanceError(f"hold_triage_unexpected_rc:{triage_proc.returncode}")

        if not triage_report_ref:
            raise HoldGovernanceError("triage_report_ref_missing")

        phase_trace.append(
            {
                "phase": "p1_p3-hold-triage",
                "status": "pass" if triage_proc.returncode == 0 else "failed",
                "return_code": triage_proc.returncode,
                "triage_action": triage_action,
                "triage_report_ref": triage_report_ref,
                "ts": now_iso(),
            }
        )

        # p4: health-maintenance
        p4_health_path = evidence_dir / "p4_health_maintenance.json"
        runtime_policy = load_json(resolve_path(root, runtime_health_policy_ref))
        max_retries = int(runtime_policy.get("max_retries", 2) or 2)
        hold_minutes = int(runtime_policy.get("max_hold_minutes", 30) or 30)

        health_status = "stable"
        maintenance_action = "monitor"
        if triage_action == "retry" and max_retries <= 0:
            health_status = "degraded"
            maintenance_action = "escalate"
        if triage_action == "fail":
            health_status = "degraded"
            maintenance_action = "escalate"

        health_payload = {
            "timestamp": now_iso(),
            "triage_action": triage_action,
            "health_status": health_status,
            "maintenance_action": maintenance_action,
            "runtime_health_policy_ref": runtime_health_policy_ref,
            "runtime_window_minutes": hold_minutes,
            "max_retries": max_retries,
        }
        dump_json(p4_health_path, health_payload)
        phase_trace.append(
            {
                "phase": "p4-health-maintenance",
                "status": "pass",
                "health_maintenance_ref": to_rel(p4_health_path, root),
                "ts": now_iso(),
            }
        )

        # p5: close-or-escalate
        p5_resolution_path = evidence_dir / "p5_hold_resolution.json"
        escalation_ref = ""
        final_owner = str(request.get("current_owner") or "qa")
        resolution_decision = "close"
        gate_decision = "pass"

        if maintenance_action == "escalate":
            p5_incident = evidence_dir / "p5_incident.json"
            p5_policy = evidence_dir / "p5_escalation_policy.json"
            p5_input = evidence_dir / "p5_escalation_input.json"
            p5_output = evidence_dir / "p5_escalation_output.json"
            p5_record = evidence_dir / "p5_escalation_record.json"

            dump_json(
                p5_incident,
                {
                    "severity": "high",
                    "reason": f"hold_triage_action={triage_action}",
                    "requested_target": "bpm",
                },
            )
            dump_json(
                p5_policy,
                {
                    "escalation_chain": ["actor", "owner", "bpm", "admin", "human"],
                },
            )
            dump_json(
                p5_input,
                {
                    "incident_ref": to_rel(p5_incident, root),
                    "escalation_policy_ref": to_rel(p5_policy, root),
                    "current_owner": final_owner,
                    "evidence_ref": runtime_log_ref,
                },
            )

            escalation_cmd = [
                sys.executable,
                "skills/system/escalation-handler/scripts/escalation_handler_runner.py",
                "--input",
                to_rel(p5_input, root),
                "--output",
                to_rel(p5_output, root),
                "--record",
                to_rel(p5_record, root),
            ]
            escalation_proc = run_cmd(escalation_cmd, root)
            escalation_payload = load_json(p5_output)
            if escalation_proc.returncode != 0:
                raise HoldGovernanceError(f"escalation_handler_failed:rc={escalation_proc.returncode}")

            escalation_ref = str(escalation_payload.get("escalation_ref") or "")
            final_owner = str(escalation_payload.get("final_owner") or final_owner)
            resolution_decision = "escalate"
            gate_decision = "fail"

        resolution_payload = {
            "timestamp": now_iso(),
            "triage_action": triage_action,
            "resolution_decision": resolution_decision,
            "final_owner": final_owner,
            "escalation_ref": escalation_ref,
            "gate_decision": gate_decision,
        }
        dump_json(p5_resolution_path, resolution_payload)

        phase_trace.append(
            {
                "phase": "p5-close-or-escalate",
                "status": "pass",
                "hold_resolution_ref": to_rel(p5_resolution_path, root),
                "resolution_decision": resolution_decision,
                "ts": now_iso(),
            }
        )

        dump_json(
            runtime_trace_path,
            {
                "timestamp": now_iso(),
                "process_id": "hold-governance",
                "status": "ok" if gate_decision == "pass" else "failed",
                "phase_trace": phase_trace,
                "input_ref": to_rel(input_path, root),
            },
        )

        output = {
            "status": "ok" if gate_decision == "pass" else "failed",
            "process_id": "hold-governance",
            "triage_action": triage_action,
            "triage_report_ref": to_rel(resolve_path(root, triage_report_ref), root) if triage_report_ref else "",
            "progress_signals_ref": to_rel(resolve_path(root, progress_signals_ref), root) if progress_signals_ref else "",
            "action_execution_ref": to_rel(resolve_path(root, action_execution_ref), root) if action_execution_ref else "",
            "health_maintenance_ref": to_rel(p4_health_path, root),
            "hold_resolution_ref": to_rel(p5_resolution_path, root),
            "escalation_ref": escalation_ref,
            "gate_decision": gate_decision,
            "evidence_ref": to_rel(evidence_dir, root),
            "runtime_trace_ref": to_rel(runtime_trace_path, root),
            "reasons": [f"triage_action={triage_action}", f"resolution={resolution_decision}"],
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 0 if gate_decision == "pass" else 2

    except Exception as exc:
        failure_reason = str(exc)
        dump_json(
            fail_closed_path,
            {
                "timestamp": now_iso(),
                "status": "failed",
                "reason": failure_reason,
                "fail_closed": True,
            },
        )
        dump_json(
            runtime_trace_path,
            {
                "timestamp": now_iso(),
                "process_id": "hold-governance",
                "status": "failed",
                "phase_trace": phase_trace,
                "reason": failure_reason,
                "fail_closed_record_ref": to_rel(fail_closed_path, root),
            },
        )
        output = {
            "status": "failed",
            "process_id": "hold-governance",
            "triage_action": "fail",
            "triage_report_ref": "",
            "health_maintenance_ref": "",
            "hold_resolution_ref": "",
            "escalation_ref": "",
            "gate_decision": "fail",
            "evidence_ref": to_rel(evidence_dir, root),
            "runtime_trace_ref": to_rel(runtime_trace_path, root),
            "fail_closed_record_ref": to_rel(fail_closed_path, root),
            "reasons": [failure_reason],
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
