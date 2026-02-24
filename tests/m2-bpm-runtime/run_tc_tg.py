#!/usr/bin/env python3
"""Run TG-SCH-001~004 and TG-EVT-001~003 for M2 BPM runtime hardening W3."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


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


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"json root must be object: {path}")
    return payload


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def append_case(cases: List[Dict[str, Any]], case_id: str, ok: bool, details: Dict[str, Any]) -> None:
    cases.append({"id": case_id, "status": "pass" if ok else "fail", "details": details})


def exists_rel(root: Path, ref: Any) -> bool:
    return isinstance(ref, str) and bool(ref.strip()) and (root / ref).exists()


def prepare_policies(root: Path, sandbox: Path) -> Dict[str, str]:
    policies_dir = sandbox / "policies"
    fixtures_dir = sandbox / "fixtures"
    ledgers_dir = sandbox / "ledgers"
    policies_dir.mkdir(parents=True, exist_ok=True)
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    ledgers_dir.mkdir(parents=True, exist_ok=True)

    schedule_policy = policies_dir / "schedule_match_policy.json"
    event_policy = policies_dir / "event_match_policy.json"
    dedupe_policy = policies_dir / "dedupe_policy.json"
    catchup_policy = policies_dir / "catchup_policy.json"
    transition_evidence = fixtures_dir / "transition_evidence.json"

    dump_json(
        schedule_policy,
        {
            "target_process_id": "development-process",
            "trigger_types": ["schedule", "heartbeat"],
            "conditions": {"trigger_source": "scheduler-main"},
        },
    )
    dump_json(
        event_policy,
        {
            "target_process_id": "development-process",
            "trigger_types": ["event"],
            "conditions": {
                "entity_type": "skill",
                "from_status": "review",
                "to_status": "active",
            },
        },
    )
    dump_json(
        dedupe_policy,
        {
            "primary_key": "source+event_id",
            "fallback_fields": [
                "trigger_source",
                "canonical_event",
                "entity_type",
                "entity_id",
                "from_status",
                "to_status",
                "emitted_by",
                "time_bucket",
            ],
        },
    )
    dump_json(
        catchup_policy,
        {
            "window_minutes_by_risk": {
                "low": 30,
                "medium": 15,
                "high": 5,
            }
        },
    )
    dump_json(
        transition_evidence,
        {
            "timestamp": now_iso(),
            "entity_type": "skill",
            "entity_id": "sys.bpm.process-instance-manager",
            "transition": "review->active",
        },
    )

    return {
        "schedule_policy": rel(schedule_policy, root),
        "event_policy": rel(event_policy, root),
        "dedupe_policy": rel(dedupe_policy, root),
        "catchup_policy": rel(catchup_policy, root),
        "transition_evidence": rel(transition_evidence, root),
        "schedule_ledger": rel(ledgers_dir / "schedule_ledger.json", root),
        "event_ledger": rel(ledgers_dir / "event_ledger.json", root),
    }


def write_schedule_payload(root: Path, case_dir: Path, event_id: str) -> str:
    payload = case_dir / "payload.json"
    dump_json(
        payload,
        {
            "event_id": event_id,
            "canonical_event": "internal.schedule.tick",
            "entity_type": "module",
            "entity_id": "M2",
            "from_status": "active",
            "to_status": "active",
            "emitted_by": "scheduler",
        },
    )
    return rel(payload, root)


def run_schedule_case(
    *,
    root: Path,
    case_id: str,
    runner: Path,
    case_dir: Path,
    input_payload: Dict[str, Any],
    instance_root: Path,
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    input_path = case_dir / "input.json"
    output_path = case_dir / "process_output.json"
    dump_json(input_path, input_payload)

    cmd = [
        sys.executable,
        str(runner),
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--evidence-dir",
        rel(case_dir, root),
        "--instance-root",
        str(instance_root),
        "--run-id",
        case_id,
    ]
    proc = run_cmd(cmd, root)
    details: Dict[str, Any] = {
        "return_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "output_ref": rel(output_path, root),
    }

    output = load_json(output_path) if output_path.exists() else {}
    details["status"] = output.get("status")
    return proc.returncode == 0, details, output


def run_event_case(
    *,
    root: Path,
    case_id: str,
    runner: Path,
    case_dir: Path,
    input_payload: Dict[str, Any],
    instance_root: Path,
) -> Tuple[int, Dict[str, Any], Dict[str, Any]]:
    input_path = case_dir / "input.json"
    output_path = case_dir / "process_output.json"
    dump_json(input_path, input_payload)

    cmd = [
        sys.executable,
        str(runner),
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--evidence-dir",
        rel(case_dir, root),
        "--instance-root",
        str(instance_root),
        "--run-id",
        case_id,
    ]
    proc = run_cmd(cmd, root)
    details: Dict[str, Any] = {
        "return_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "output_ref": rel(output_path, root),
    }
    output = load_json(output_path) if output_path.exists() else {}
    details["status"] = output.get("status")
    return proc.returncode, details, output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TG trigger runtime test cases")
    parser.add_argument(
        "--schedule-runner",
        default="processes/control/trigger-schedule-runtime/scripts/trigger_schedule_runtime_runner.py",
        help="repo-relative schedule runtime runner path",
    )
    parser.add_argument(
        "--event-runner",
        default="processes/control/trigger-event-runtime/scripts/trigger_event_runtime_runner.py",
        help="repo-relative event runtime runner path",
    )
    parser.add_argument(
        "--report",
        default="runtime_data/execution/evidence/bpm-runtime/w3_tc_tg_report.json",
        help="repo-relative report output path",
    )
    parser.add_argument(
        "--evidence-root",
        default="runtime_data/execution/evidence/bpm-runtime/w3_trigger_runtime_cases",
        help="repo-relative evidence root",
    )
    parser.add_argument(
        "--sandbox-root",
        default="tmp/m2-bpm-runtime/tc-tg-sandbox",
        help="repo-relative sandbox root",
    )
    parser.add_argument(
        "--instance-root",
        default="tmp/m2-bpm-runtime/tc-tg-sandbox/instances",
        help="repo-relative instance root",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    schedule_runner = (root / args.schedule_runner).resolve()
    event_runner = (root / args.event_runner).resolve()
    report_path = (root / args.report).resolve()
    evidence_root = (root / args.evidence_root).resolve()
    sandbox_root = (root / args.sandbox_root).resolve()
    instance_root = (root / args.instance_root).resolve()

    if not schedule_runner.exists():
        raise RuntimeError(f"schedule runner not found: {schedule_runner}")
    if not event_runner.exists():
        raise RuntimeError(f"event runner not found: {event_runner}")

    if sandbox_root.exists():
        shutil.rmtree(sandbox_root)
    sandbox_root.mkdir(parents=True, exist_ok=True)

    if instance_root.exists():
        shutil.rmtree(instance_root)
    instance_root.mkdir(parents=True, exist_ok=True)

    if evidence_root.exists():
        shutil.rmtree(evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=True)

    refs = prepare_policies(root, sandbox_root)
    cases: List[Dict[str, Any]] = []
    runtime_outputs: Dict[str, Dict[str, Any]] = {}

    # TG-SCH-001
    sch1_dir = evidence_root / "TG-SCH-001"
    sch1_dir.mkdir(parents=True, exist_ok=True)
    sch1_payload = write_schedule_payload(root, sch1_dir, "sch-001")
    sch1_ok, sch1_details, sch1_out = run_schedule_case(
        root=root,
        case_id="TG-SCH-001",
        runner=schedule_runner,
        case_dir=sch1_dir,
        instance_root=instance_root,
        input_payload={
            "trigger_type": "schedule",
            "trigger_source": "scheduler-main",
            "payload_ref": sch1_payload,
            "received_at": now_iso(),
            "match_policy_ref": refs["schedule_policy"],
            "dedupe_policy_ref": refs["dedupe_policy"],
            "catchup_policy_ref": refs["catchup_policy"],
            "dedupe_ledger_ref": refs["schedule_ledger"],
            "has_anomaly": True,
            "missed": False,
            "delivery_policy": "exception-only",
        },
    )
    sch1_ok = sch1_ok and exists_rel(root, sch1_out.get("trigger_receipt_ref")) and exists_rel(root, sch1_out.get("admin_forward_ref"))
    sch1_details.update(
        {
            "trigger_receipt_ref": sch1_out.get("trigger_receipt_ref"),
            "admin_forward_ref": sch1_out.get("admin_forward_ref"),
            "instance_id": sch1_out.get("instance_id"),
        }
    )
    append_case(cases, "TG-SCH-001", sch1_ok, sch1_details)
    runtime_outputs["TG-SCH-001"] = sch1_out

    # TG-SCH-002
    sch2_dir = evidence_root / "TG-SCH-002"
    sch2_dir.mkdir(parents=True, exist_ok=True)
    sch2_payload = write_schedule_payload(root, sch2_dir, "sch-002")
    sch2_ok, sch2_details, sch2_out = run_schedule_case(
        root=root,
        case_id="TG-SCH-002",
        runner=schedule_runner,
        case_dir=sch2_dir,
        instance_root=instance_root,
        input_payload={
            "trigger_type": "schedule",
            "trigger_source": "scheduler-main",
            "payload_ref": sch2_payload,
            "received_at": now_iso(),
            "match_policy_ref": refs["schedule_policy"],
            "dedupe_policy_ref": refs["dedupe_policy"],
            "catchup_policy_ref": refs["catchup_policy"],
            "dedupe_ledger_ref": refs["schedule_ledger"],
            "has_anomaly": False,
            "missed": False,
            "delivery_policy": "exception-only",
        },
    )
    sch2_ok = sch2_ok and exists_rel(root, sch2_out.get("trigger_ledger_ref"))
    sch2_details.update(
        {
            "trigger_ledger_ref": sch2_out.get("trigger_ledger_ref"),
            "instance_id": sch2_out.get("instance_id"),
        }
    )
    append_case(cases, "TG-SCH-002", sch2_ok, sch2_details)
    runtime_outputs["TG-SCH-002"] = sch2_out

    # TG-SCH-003
    sch3_dir = evidence_root / "TG-SCH-003"
    sch3_dir.mkdir(parents=True, exist_ok=True)
    sch3_payload = write_schedule_payload(root, sch3_dir, "sch-003")
    sch3_ok, sch3_details, sch3_out = run_schedule_case(
        root=root,
        case_id="TG-SCH-003",
        runner=schedule_runner,
        case_dir=sch3_dir,
        instance_root=instance_root,
        input_payload={
            "trigger_type": "schedule",
            "trigger_source": "scheduler-main",
            "payload_ref": sch3_payload,
            "received_at": now_iso(),
            "match_policy_ref": refs["schedule_policy"],
            "dedupe_policy_ref": refs["dedupe_policy"],
            "catchup_policy_ref": refs["catchup_policy"],
            "dedupe_ledger_ref": refs["schedule_ledger"],
            "owner_override": True,
            "override_reason": "owner cancelled this tick",
        },
    )
    sch3_ok = sch3_ok and exists_rel(root, sch3_out.get("override_decision_ref")) and exists_rel(root, sch3_out.get("override_reason_ref"))
    sch3_details.update(
        {
            "override_decision_ref": sch3_out.get("override_decision_ref"),
            "override_reason_ref": sch3_out.get("override_reason_ref"),
            "instance_id": sch3_out.get("instance_id"),
        }
    )
    append_case(cases, "TG-SCH-003", sch3_ok, sch3_details)
    runtime_outputs["TG-SCH-003"] = sch3_out

    # TG-SCH-004
    sch4_dir = evidence_root / "TG-SCH-004"
    sch4_dir.mkdir(parents=True, exist_ok=True)
    sch4_payload = write_schedule_payload(root, sch4_dir, "sch-004")
    sch4_runtime_state = sch4_dir / "runtime_state.json"
    sch4_expected = datetime.now(timezone.utc) - timedelta(minutes=10)
    dump_json(
        sch4_runtime_state,
        {
            "observed_at": now_iso(),
            "risk_level": "low",
            "trigger_type": "schedule",
        },
    )
    sch4_ok, sch4_details, sch4_out = run_schedule_case(
        root=root,
        case_id="TG-SCH-004",
        runner=schedule_runner,
        case_dir=sch4_dir,
        instance_root=instance_root,
        input_payload={
            "trigger_type": "schedule",
            "trigger_source": "scheduler-main",
            "payload_ref": sch4_payload,
            "received_at": now_iso(),
            "match_policy_ref": refs["schedule_policy"],
            "dedupe_policy_ref": refs["dedupe_policy"],
            "catchup_policy_ref": refs["catchup_policy"],
            "dedupe_ledger_ref": refs["schedule_ledger"],
            "missed": True,
            "expected_run_at": sch4_expected.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "runtime_state_ref": rel(sch4_runtime_state, root),
            "risk_level": "low",
        },
    )
    sch4_ok = sch4_ok and sch4_out.get("catchup_decision") == "run" and exists_rel(root, sch4_out.get("catchup_run_ref"))
    sch4_details.update(
        {
            "catchup_decision": sch4_out.get("catchup_decision"),
            "catchup_run_ref": sch4_out.get("catchup_run_ref"),
        }
    )
    append_case(cases, "TG-SCH-004", sch4_ok, sch4_details)
    runtime_outputs["TG-SCH-004"] = sch4_out

    # TG-EVT-001
    evt1_dir = evidence_root / "TG-EVT-001"
    evt1_dir.mkdir(parents=True, exist_ok=True)
    evt1_rc, evt1_details, evt1_out = run_event_case(
        root=root,
        case_id="TG-EVT-001",
        runner=event_runner,
        case_dir=evt1_dir,
        instance_root=instance_root,
        input_payload={
            "event_id": "evt-001",
            "event_time": now_iso(),
            "entity_type": "skill",
            "entity_id": "sys.bpm.process-instance-manager",
            "from_status": "review",
            "to_status": "active",
            "transition_evidence_ref": refs["transition_evidence"],
            "trigger_source": "lifecycle",
            "emitted_by": "hr",
            "match_policy_ref": refs["event_policy"],
            "dedupe_policy_ref": refs["dedupe_policy"],
            "catchup_policy_ref": refs["catchup_policy"],
            "dedupe_ledger_ref": refs["event_ledger"],
        },
    )
    evt1_ok = evt1_rc == 0 and exists_rel(root, evt1_out.get("event_ref")) and exists_rel(root, evt1_out.get("trigger_receipt_ref"))
    evt1_details.update(
        {
            "event_ref": evt1_out.get("event_ref"),
            "trigger_receipt_ref": evt1_out.get("trigger_receipt_ref"),
            "instance_id": evt1_out.get("instance_id"),
        }
    )
    append_case(cases, "TG-EVT-001", evt1_ok, evt1_details)
    runtime_outputs["TG-EVT-001"] = evt1_out

    # TG-EVT-002
    evt2_dir = evidence_root / "TG-EVT-002"
    evt2_dir.mkdir(parents=True, exist_ok=True)
    evt2_rc, evt2_details, evt2_out = run_event_case(
        root=root,
        case_id="TG-EVT-002",
        runner=event_runner,
        case_dir=evt2_dir,
        instance_root=instance_root,
        input_payload={
            "event_id": "evt-001",
            "event_time": now_iso(),
            "entity_type": "skill",
            "entity_id": "sys.bpm.process-instance-manager",
            "from_status": "review",
            "to_status": "active",
            "transition_evidence_ref": refs["transition_evidence"],
            "trigger_source": "lifecycle",
            "emitted_by": "hr",
            "match_policy_ref": refs["event_policy"],
            "dedupe_policy_ref": refs["dedupe_policy"],
            "catchup_policy_ref": refs["catchup_policy"],
            "dedupe_ledger_ref": refs["event_ledger"],
        },
    )
    evt2_ok = (
        evt2_rc == 0
        and evt2_out.get("dedupe_decision") == "reject"
        and exists_rel(root, evt2_out.get("dedupe_key_ref"))
        and exists_rel(root, evt2_out.get("dedupe_reject_log_ref"))
    )
    evt2_details.update(
        {
            "dedupe_decision": evt2_out.get("dedupe_decision"),
            "dedupe_key_ref": evt2_out.get("dedupe_key_ref"),
            "dedupe_reject_log_ref": evt2_out.get("dedupe_reject_log_ref"),
        }
    )
    append_case(cases, "TG-EVT-002", evt2_ok, evt2_details)
    runtime_outputs["TG-EVT-002"] = evt2_out

    # TG-EVT-003
    evt3_dir = evidence_root / "TG-EVT-003"
    evt3_dir.mkdir(parents=True, exist_ok=True)
    evt3_rc, evt3_details, evt3_out = run_event_case(
        root=root,
        case_id="TG-EVT-003",
        runner=event_runner,
        case_dir=evt3_dir,
        instance_root=instance_root,
        input_payload={
            "event_id": "evt-003",
            "event_time": now_iso(),
            "entity_type": "skill",
            "entity_id": "sys.bpm.catchup-scheduler",
            "from_status": "review",
            "to_status": "active",
            "trigger_source": "lifecycle",
            "emitted_by": "hr",
            "match_policy_ref": refs["event_policy"],
            "dedupe_policy_ref": refs["dedupe_policy"],
            "catchup_policy_ref": refs["catchup_policy"],
            "dedupe_ledger_ref": refs["event_ledger"],
        },
    )
    evt3_ok = evt3_rc == 2 and exists_rel(root, evt3_out.get("fail_closed_record_ref")) and exists_rel(root, evt3_out.get("backfill_request_ref"))
    evt3_details.update(
        {
            "fail_closed_record_ref": evt3_out.get("fail_closed_record_ref"),
            "backfill_request_ref": evt3_out.get("backfill_request_ref"),
        }
    )
    append_case(cases, "TG-EVT-003", evt3_ok, evt3_details)
    runtime_outputs["TG-EVT-003"] = evt3_out

    # Session isolation check
    session_map: Dict[str, str] = {}
    isolation_errors: List[str] = []
    checked_cases: List[str] = []
    for case_id, payload in runtime_outputs.items():
        instance_id = str(payload.get("instance_id") or "")
        trace_ref = payload.get("runtime_trace_ref")
        if not instance_id or instance_id.startswith("virtual-"):
            continue
        if not isinstance(trace_ref, str) or not trace_ref.strip():
            isolation_errors.append(f"{case_id}:missing_runtime_trace_ref")
            continue

        trace_path = root / trace_ref
        if not trace_path.exists():
            isolation_errors.append(f"{case_id}:runtime_trace_missing")
            continue

        runtime_trace = load_json(trace_path)
        session_id = str(runtime_trace.get("session_id") or "")
        if not session_id:
            isolation_errors.append(f"{case_id}:session_id_missing")
            continue

        checked_cases.append(case_id)
        existing = session_map.get(session_id)
        if existing and existing != instance_id:
            isolation_errors.append(f"session_reused:{session_id}:{existing}->{instance_id}")
        else:
            session_map[session_id] = instance_id

    isolation_ok = len(isolation_errors) == 0

    passed = sum(1 for case in cases if case["status"] == "pass")
    failed = len(cases) - passed
    report = {
        "ts": now_iso(),
        "suite": "TG-SCH-001~004 + TG-EVT-001~003",
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "cases": cases,
        "session_isolation": {
            "status": "pass" if isolation_ok else "fail",
            "checked_cases": checked_cases,
            "errors": isolation_errors,
        },
        "evidence_root": rel(evidence_root, root),
    }

    dump_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if failed == 0 and isolation_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
