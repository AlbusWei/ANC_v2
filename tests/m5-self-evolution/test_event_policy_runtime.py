#!/usr/bin/env python3
"""M5 事件策略执行回归（Batch 6）。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


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
    """Runner 输入统一使用绝对路径，避免 pytest tmp 目录相对路径问题。"""
    return str(path.resolve())


def make_repo_case_dir(case_key: str, tmp_path: Path) -> Path:
    """在仓库内创建测试工作目录，避免 runner 的相对路径转换失败。"""
    root = repo_root()
    case_dir = root / "tmp" / "m5-self-evolution-tests" / f"{case_key}-{tmp_path.name}"
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir


def run_cmd(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def run_trigger_event_case(case_dir: Path, payload: Dict[str, Any], run_id: str) -> tuple[subprocess.CompletedProcess[str], Dict[str, Any]]:
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


def prepare_common_policy_files(base_dir: Path) -> Dict[str, str]:
    policies_dir = base_dir / "policies"
    policies_dir.mkdir(parents=True, exist_ok=True)

    match_policy = policies_dir / "event_match_policy.json"
    dedupe_policy = policies_dir / "dedupe_policy.json"
    catchup_policy = policies_dir / "catchup_policy.json"

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

    return {
        "match_policy_ref": as_ref(match_policy),
        "dedupe_policy_ref": as_ref(dedupe_policy),
        "catchup_policy_ref": as_ref(catchup_policy),
    }


def test_unmatched_event_must_write_receipt(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("unmatched", tmp_path)

    refs = prepare_common_policy_files(case_dir)

    routing_policy = case_dir / "event-routing-policy.json"
    escalation_chain = case_dir / "escalation-chain-policy.json"
    escalation_policy = case_dir / "event-escalation-policy.json"
    transition_evidence = case_dir / "transition_evidence.json"

    dump_json(
        routing_policy,
        {
            "version": "0.1.0",
            "routes": [
                {
                    "route_id": "only-m1-pass",
                    "event_name": "m1.gate.pass",
                    **refs,
                }
            ],
        },
    )
    dump_json(escalation_chain, {"escalation_chain": ["actor", "owner", "bpm", "admin", "human"]})
    dump_json(
        escalation_policy,
        {
            "version": "0.1.0",
            "escalation_chain_policy_ref": as_ref(escalation_chain),
            "rules": [],
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

    proc, output = run_trigger_event_case(
        case_dir,
        {
            "event_id": "evt-unmatched-001",
            "event_name": "m5.proposal.accepted",
            "module": "m5",
            "severity": "warning",
            "event_time": now_iso(),
            "entity_type": "skill",
            "entity_id": "sys.bpm.process-instance-manager",
            "from_status": "review",
            "to_status": "active",
            "transition_evidence_ref": as_ref(transition_evidence),
            "trigger_source": "domain-hook",
            "emitted_by": "hr",
            "owner_agent_id": "hr",
            "event_routing_policy_ref": as_ref(routing_policy),
            "event_escalation_policy_ref": as_ref(escalation_policy),
            "dedupe_ledger_ref": as_ref(case_dir / "dedupe_ledger.json"),
        },
        run_id="TC-M5-HOOK-POLICY-001",
    )

    assert proc.returncode == 0, proc.stderr
    unmatched_ref = str(output.get("unmatched_event_receipt_ref") or "")
    assert unmatched_ref, output
    unmatched_path = root / unmatched_ref
    assert unmatched_path.exists(), unmatched_ref
    receipt = load_json(unmatched_path)
    assert receipt.get("reason") == "route_unmatched"
    assert output.get("dedupe_decision") == "skip"


def test_dedupe_conflict_must_fail_closed(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("dedupe-conflict", tmp_path)

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
            "trigger_source": "lifecycle",
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
    dump_json(
        match_policy,
        {
            "target_process_id": "development-process",
            "trigger_types": ["event"],
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
        ledger,
        {
            "entries": {
                "primary:lifecycle|evt-conflict-001": {
                    "trigger_id": "trg-old-primary",
                    "created_at": now_iso(),
                    "source": "lifecycle",
                    "decision": "allow",
                },
                "fallback:lifecycle|m4.lifecycle.transition.approved|skill|sys.bpm.process-instance-manager|review|active|hr|20260303T1500": {
                    "trigger_id": "trg-old-fallback",
                    "created_at": now_iso(),
                    "source": "lifecycle",
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


def test_escalation_threshold_rule_must_trigger_after_threshold(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("escalation-threshold", tmp_path)

    refs = prepare_common_policy_files(case_dir)

    routing_policy = case_dir / "event-routing-policy.json"
    escalation_chain = case_dir / "escalation-chain-policy.json"
    escalation_policy = case_dir / "event-escalation-policy.json"
    transition_evidence = case_dir / "transition_evidence.json"
    escalation_counter = case_dir / "escalation_counter.json"
    dedupe_ledger = case_dir / "dedupe_ledger.json"

    dump_json(
        routing_policy,
        {
            "version": "0.1.0",
            "routes": [
                {
                    "route_id": "m1-gate-failed-route",
                    "event_name": "m1.gate.failed",
                    "module": "m1",
                    **refs,
                }
            ],
        },
    )
    dump_json(escalation_chain, {"escalation_chain": ["actor", "owner", "bpm", "admin", "human"]})
    dump_json(
        escalation_policy,
        {
            "version": "0.1.0",
            "escalation_chain_policy_ref": as_ref(escalation_chain),
            "rules": [
                {
                    "rule_id": "m1-gate-failed-burst",
                    "event_name": "m1.gate.failed",
                    "strategy": "threshold",
                    "threshold": 2,
                    "severity": "high",
                    "reason_template": "m1 gate failed burst",
                    "requested_target": "admin",
                }
            ],
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

    base_payload = {
        "event_name": "m1.gate.failed",
        "module": "m1",
        "severity": "warning",
        "entity_type": "skill",
        "entity_id": "sys.bpm.process-instance-manager",
        "from_status": "review",
        "to_status": "active",
        "transition_evidence_ref": as_ref(transition_evidence),
        "trigger_source": "domain-hook",
        "emitted_by": "qa",
        "owner_agent_id": "owner",
        "event_routing_policy_ref": as_ref(routing_policy),
        "event_escalation_policy_ref": as_ref(escalation_policy),
        "escalation_counter_ref": as_ref(escalation_counter),
        "dedupe_ledger_ref": as_ref(dedupe_ledger),
    }

    proc1, out1 = run_trigger_event_case(
        case_dir,
        {
            **base_payload,
            "event_id": "evt-threshold-001",
            "event_time": now_iso(),
        },
        run_id="TC-M5-HOOK-POLICY-003-A",
    )
    assert proc1.returncode == 0, proc1.stderr
    assert str(out1.get("escalation_ref") or "") == ""

    proc2, out2 = run_trigger_event_case(
        case_dir,
        {
            **base_payload,
            "event_id": "evt-threshold-002",
            "event_time": now_iso(),
        },
        run_id="TC-M5-HOOK-POLICY-003-B",
    )
    assert proc2.returncode == 0, proc2.stderr
    escalation_ref = str(out2.get("escalation_ref") or "")
    assert escalation_ref, out2
    escalation_path = root / escalation_ref
    assert escalation_path.exists(), escalation_ref
