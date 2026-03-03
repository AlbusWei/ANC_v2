#!/usr/bin/env python3
"""M5 Batch 10 准入回归：TC-M5-001~007 + TC-M5-HOOK-001~004。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"json root must be object: {path}")
    return payload


def as_ref(path: Path) -> str:
    return str(path.resolve())


def run_cmd(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def make_repo_case_dir(case_key: str, tmp_path: Path) -> Path:
    root = repo_root()
    case_dir = root / "tmp" / "m5-self-evolution-tests" / f"{case_key}-{tmp_path.name}"
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir


def prepare_policy_bundle(case_dir: Path, *, route_event: str, route_module: str, with_default: bool = True) -> Dict[str, str]:
    policies_dir = case_dir / "policies"
    policies_dir.mkdir(parents=True, exist_ok=True)

    match_policy = policies_dir / "event_match_policy.json"
    dedupe_policy = policies_dir / "dedupe_policy.json"
    catchup_policy = policies_dir / "catchup_policy.json"
    routing_policy = case_dir / "event-routing-policy.json"

    dump_json(
        match_policy,
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

    routing: Dict[str, Any] = {
        "version": "0.1.0",
        "routes": [
            {
                "route_id": f"{route_module}-{route_event}",
                "event_name": route_event,
                "module": route_module,
                "match_policy_ref": as_ref(match_policy),
                "dedupe_policy_ref": as_ref(dedupe_policy),
                "catchup_policy_ref": as_ref(catchup_policy),
            }
        ],
    }
    if with_default:
        routing["default_route"] = {
            "route_id": "default",
            "match_policy_ref": as_ref(match_policy),
            "dedupe_policy_ref": as_ref(dedupe_policy),
            "catchup_policy_ref": as_ref(catchup_policy),
        }
    dump_json(routing_policy, routing)
    return {
        "event_routing_policy_ref": as_ref(routing_policy),
        "dedupe_policy_ref": as_ref(dedupe_policy),
        "catchup_policy_ref": as_ref(catchup_policy),
    }


def prepare_escalation_policy(case_dir: Path, *, threshold: int = 1) -> str:
    chain = case_dir / "escalation-chain-policy.json"
    policy = case_dir / "event-escalation-policy.json"
    dump_json(chain, {"escalation_chain": ["actor", "owner", "bpm", "admin", "human"]})
    dump_json(
        policy,
        {
            "version": "0.1.0",
            "escalation_chain_policy_ref": as_ref(chain),
            "rules": [
                {
                    "rule_id": "m1-gate-failed-threshold",
                    "event_name": "m1.gate.failed",
                    "module": "m1",
                    "strategy": "threshold",
                    "threshold": threshold,
                    "severity": "high",
                    "reason_template": "m1 gate failed reached threshold",
                    "requested_target": "admin",
                }
            ],
        },
    )
    return as_ref(policy)


def run_trigger_event_case(case_dir: Path, payload: Dict[str, Any], run_id: str) -> Tuple[subprocess.CompletedProcess[str], Dict[str, Any]]:
    root = repo_root()
    input_path = case_dir / f"{run_id}_input.json"
    output_path = case_dir / f"{run_id}_output.json"
    evidence_dir = case_dir / f"{run_id}_evidence"
    instance_root = case_dir / "instances"
    dump_json(input_path, payload)

    cmd = [
        sys.executable,
        "processes/control/trigger-event-runtime/scripts/trigger_event_runtime_runner.py",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--evidence-dir",
        str(evidence_dir),
        "--instance-root",
        str(instance_root),
        "--run-id",
        run_id,
    ]
    proc = run_cmd(cmd, root)
    output = load_json(output_path)
    return proc, output


def make_transition_evidence(case_dir: Path, name: str = "transition_evidence.json") -> str:
    evidence = case_dir / name
    dump_json(
        evidence,
        {
            "timestamp": now_iso(),
            "entity_type": "skill",
            "entity_id": "sys.bpm.process-instance-manager",
            "transition": "review->active",
        },
    )
    return as_ref(evidence)


def make_base_event_payload(case_dir: Path, *, trigger_source: str, event_name: str, module: str) -> Dict[str, Any]:
    policy_refs = prepare_policy_bundle(case_dir, route_event=event_name, route_module=module, with_default=True)
    return {
        "event_id": f"evt-{event_name.replace('.', '-')}-001",
        "event_name": event_name,
        "module": module,
        "severity": "warning",
        "event_time": now_iso(),
        "entity_type": "skill",
        "entity_id": "sys.bpm.process-instance-manager",
        "from_status": "review",
        "to_status": "active",
        "transition_evidence_ref": make_transition_evidence(case_dir),
        "trigger_source": trigger_source,
        "emitted_by": "hr",
        "owner_agent_id": "owner",
        "event_routing_policy_ref": policy_refs["event_routing_policy_ref"],
        "dedupe_ledger_ref": as_ref(case_dir / "dedupe_ledger.json"),
    }


def assert_ref_exists(root: Path, ref: Any) -> Path:
    assert isinstance(ref, str) and ref.strip(), ref
    path = root / ref
    assert path.exists(), ref
    return path


def test_tc_m5_001_main_chain_happy_path(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("tc-m5-001", tmp_path)
    payload = make_base_event_payload(
        case_dir,
        trigger_source="domain-hook",
        event_name="m3.implementation.completed",
        module="m3",
    )

    proc, output = run_trigger_event_case(case_dir, payload, run_id="TC-M5-001")
    assert proc.returncode == 0, proc.stderr
    assert output.get("status") == "ok"
    assert output.get("dedupe_decision") == "allow"
    assert_ref_exists(root, output.get("trigger_receipt_ref"))
    assert_ref_exists(root, output.get("runtime_trace_ref"))
    assert str(output.get("unmatched_event_receipt_ref") or "") == ""


def test_tc_m5_002_escalation_threshold(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("tc-m5-002", tmp_path)
    payload = make_base_event_payload(
        case_dir,
        trigger_source="domain-hook",
        event_name="m1.gate.failed",
        module="m1",
    )
    payload["event_escalation_policy_ref"] = prepare_escalation_policy(case_dir, threshold=1)
    payload["escalation_counter_ref"] = as_ref(case_dir / "escalation_counter.json")

    proc, output = run_trigger_event_case(case_dir, payload, run_id="TC-M5-002")
    assert proc.returncode == 0, proc.stderr
    escalation_ref = str(output.get("escalation_ref") or "")
    assert escalation_ref, output
    assert_ref_exists(root, escalation_ref)


def test_tc_m5_003_missing_evidence_fail_closed(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("tc-m5-003", tmp_path)
    payload = make_base_event_payload(
        case_dir,
        trigger_source="domain-hook",
        event_name="m3.implementation.completed",
        module="m3",
    )
    payload.pop("transition_evidence_ref", None)
    payload.pop("evidence_ref", None)

    proc, output = run_trigger_event_case(case_dir, payload, run_id="TC-M5-003")
    assert proc.returncode == 2
    assert output.get("status") == "failed"
    assert output.get("reason") == "missing_transition_evidence_ref"
    assert_ref_exists(root, output.get("fail_closed_record_ref"))


def test_tc_m5_004_unreachable_evidence_fail_closed(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("tc-m5-004", tmp_path)
    payload = make_base_event_payload(
        case_dir,
        trigger_source="domain-hook",
        event_name="m3.implementation.completed",
        module="m3",
    )
    payload["transition_evidence_ref"] = as_ref(case_dir / "missing_transition.json")

    proc, output = run_trigger_event_case(case_dir, payload, run_id="TC-M5-004")
    assert proc.returncode == 2
    assert output.get("status") == "failed"
    assert output.get("reason") == "transition_evidence_unreachable"
    assert_ref_exists(root, output.get("fail_closed_record_ref"))


def test_tc_m5_005_unmatched_receipt_must_exist(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("tc-m5-005", tmp_path)
    policy_refs = prepare_policy_bundle(
        case_dir,
        route_event="m1.gate.pass",
        route_module="m1",
        with_default=False,
    )
    payload = {
        "event_id": "evt-tc-m5-005",
        "event_name": "m5.proposal.accepted",
        "module": "m5",
        "severity": "info",
        "event_time": now_iso(),
        "entity_type": "skill",
        "entity_id": "sys.bpm.process-instance-manager",
        "from_status": "review",
        "to_status": "active",
        "transition_evidence_ref": make_transition_evidence(case_dir),
        "trigger_source": "domain-hook",
        "emitted_by": "hr",
        "owner_agent_id": "owner",
        "event_routing_policy_ref": policy_refs["event_routing_policy_ref"],
        "dedupe_ledger_ref": as_ref(case_dir / "dedupe_ledger.json"),
    }

    proc, output = run_trigger_event_case(case_dir, payload, run_id="TC-M5-005")
    assert proc.returncode == 0, proc.stderr
    assert output.get("status") == "ok"
    assert output.get("dedupe_decision") == "skip"
    assert_ref_exists(root, output.get("unmatched_event_receipt_ref"))


def test_tc_m5_006_dedupe_conflict_fail_closed(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("tc-m5-006", tmp_path)

    canonical = case_dir / "canonical_trigger.json"
    match_policy = case_dir / "match_policy.json"
    dedupe_policy = case_dir / "dedupe_policy.json"
    ledger = case_dir / "ledger.json"
    matcher_input = case_dir / "input.json"
    matcher_output = case_dir / "output.json"
    dedupe_key = case_dir / "dedupe_key.json"
    evidence = case_dir / "matcher_evidence.json"

    dump_json(
        canonical,
        {
            "trigger_id": "trg-conflict-001",
            "trigger_type": "event",
            "trigger_source": "domain-hook",
            "received_at": now_iso(),
            "time_bucket": "20260303T1500",
            "event_id": "evt-conflict-001",
            "canonical_event": "m4.lifecycle.transition.approved",
            "entity_type": "skill",
            "entity_id": "sys.bpm.process-instance-manager",
            "from_status": "review",
            "to_status": "active",
            "emitted_by": "hr",
        },
    )
    dump_json(match_policy, {"target_process_id": "development-process", "trigger_types": ["event"]})
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
        ledger,
        {
            "entries": {
                "primary:domain-hook|evt-conflict-001": {
                    "trigger_id": "trg-old-primary",
                    "created_at": now_iso(),
                    "source": "domain-hook",
                    "decision": "allow",
                },
                "fallback:domain-hook|m4.lifecycle.transition.approved|skill|sys.bpm.process-instance-manager|review|active|hr|20260303T1500": {
                    "trigger_id": "trg-old-fallback",
                    "created_at": now_iso(),
                    "source": "domain-hook",
                    "decision": "allow",
                },
            }
        },
    )
    dump_json(
        matcher_input,
        {
            "canonical_trigger_ref": as_ref(canonical),
            "match_policy_ref": as_ref(match_policy),
            "dedupe_policy_ref": as_ref(dedupe_policy),
        },
    )

    cmd = [
        sys.executable,
        "skills/system/trigger-matcher-dedupe/scripts/trigger_matcher_dedupe_runner.py",
        "--input",
        str(matcher_input),
        "--output",
        str(matcher_output),
        "--dedupe-key",
        str(dedupe_key),
        "--evidence",
        str(evidence),
        "--ledger",
        str(ledger),
    ]
    proc = run_cmd(cmd, root)
    payload = load_json(matcher_output)

    assert proc.returncode == 2, proc.stderr
    assert payload.get("dedupe_decision") == "fail"
    assert payload.get("reason") == "dedupe_conflict_unresolved"


def test_tc_m5_007_duplicate_event_reject(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("tc-m5-007", tmp_path)
    payload = make_base_event_payload(
        case_dir,
        trigger_source="domain-hook",
        event_name="m3.implementation.completed",
        module="m3",
    )
    payload["event_id"] = "evt-tc-m5-007"
    dump_json(
        case_dir / "dedupe_ledger.json",
        {
            "entries": {
                "primary:domain-hook|evt-tc-m5-007": {
                    "trigger_id": "trg-old-evt",
                    "created_at": now_iso(),
                    "source": "domain-hook",
                    "decision": "allow",
                }
            }
        },
    )

    proc, output = run_trigger_event_case(case_dir, payload, run_id="TC-M5-007")
    assert proc.returncode == 0, proc.stderr
    assert output.get("status") == "ok"
    assert output.get("dedupe_decision") == "reject"
    assert_ref_exists(root, output.get("trigger_receipt_ref"))
    assert str(output.get("instance_id") or "").startswith("virtual-")


def test_tc_m5_hook_001_platform_hook_happy_path(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("tc-m5-hook-001", tmp_path)
    payload = make_base_event_payload(
        case_dir,
        trigger_source="platform-hook",
        event_name="m3.implementation.completed",
        module="m3",
    )

    proc, output = run_trigger_event_case(case_dir, payload, run_id="TC-M5-HOOK-001")
    assert proc.returncode == 0, proc.stderr
    assert output.get("status") == "ok"
    assert_ref_exists(root, output.get("trigger_receipt_ref"))


def test_tc_m5_hook_002_missing_evidence_fail_closed(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("tc-m5-hook-002", tmp_path)
    payload = make_base_event_payload(
        case_dir,
        trigger_source="platform-hook",
        event_name="m3.implementation.completed",
        module="m3",
    )
    payload.pop("transition_evidence_ref", None)
    payload.pop("evidence_ref", None)

    proc, output = run_trigger_event_case(case_dir, payload, run_id="TC-M5-HOOK-002")
    assert proc.returncode == 2
    assert output.get("status") == "failed"
    assert output.get("reason") == "missing_transition_evidence_ref"
    assert_ref_exists(root, output.get("fail_closed_record_ref"))


def test_tc_m5_hook_003_dedupe_conflict_fail_closed(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("tc-m5-hook-003", tmp_path)
    payload = make_base_event_payload(
        case_dir,
        trigger_source="platform-hook",
        event_name="m3.implementation.completed",
        module="m3",
    )
    payload["event_id"] = "evt-hook-conflict-001"
    payload["received_at"] = "2026-03-03T15:00:20Z"

    dump_json(
        case_dir / "dedupe_ledger.json",
        {
            "entries": {
                "primary:platform-hook|evt-hook-conflict-001": {
                    "trigger_id": "trg-old-primary",
                    "created_at": now_iso(),
                    "source": "platform-hook",
                    "decision": "allow",
                },
                "fallback:platform-hook|m3.implementation.completed|skill|sys.bpm.process-instance-manager|review|active|hr|20260303T1500": {
                    "trigger_id": "trg-old-fallback",
                    "created_at": now_iso(),
                    "source": "platform-hook",
                    "decision": "allow",
                },
            }
        },
    )

    proc, output = run_trigger_event_case(case_dir, payload, run_id="TC-M5-HOOK-003")
    assert proc.returncode == 2
    assert output.get("status") == "failed"
    assert output.get("reason") == "p2_matcher_failed"
    assert_ref_exists(root, output.get("fail_closed_record_ref"))


def test_tc_m5_hook_004_unmatched_receipt_must_exist(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("tc-m5-hook-004", tmp_path)
    policy_refs = prepare_policy_bundle(
        case_dir,
        route_event="m1.gate.pass",
        route_module="m1",
        with_default=False,
    )
    payload = {
        "event_id": "evt-tc-m5-hook-004",
        "event_name": "asset.health.degraded",
        "module": "runtime-monitor",
        "severity": "warning",
        "event_time": now_iso(),
        "entity_type": "skill",
        "entity_id": "sys.bpm.process-instance-manager",
        "from_status": "review",
        "to_status": "active",
        "transition_evidence_ref": make_transition_evidence(case_dir),
        "trigger_source": "platform-hook",
        "emitted_by": "hr",
        "owner_agent_id": "owner",
        "event_routing_policy_ref": policy_refs["event_routing_policy_ref"],
        "dedupe_ledger_ref": as_ref(case_dir / "dedupe_ledger.json"),
    }

    proc, output = run_trigger_event_case(case_dir, payload, run_id="TC-M5-HOOK-004")
    assert proc.returncode == 0, proc.stderr
    assert output.get("status") == "ok"
    assert_ref_exists(root, output.get("unmatched_event_receipt_ref"))
