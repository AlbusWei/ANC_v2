#!/usr/bin/env python3
"""M5 Batch 7: 关键 runner 结束点领域事件产出回归。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


REQUIRED_EVENT_FIELDS = [
    "contract_version",
    "event_id",
    "event_name",
    "event_time",
    "module",
    "trigger_source",
    "severity",
    "evidence_ref",
    "owner_agent_id",
    "dedupe_key",
]


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


def run_cmd(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def make_repo_case_dir(case_key: str, tmp_path: Path) -> Path:
    root = repo_root()
    case_dir = root / "tmp" / "m5-self-evolution-tests" / f"{case_key}-{tmp_path.name}"
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir


def assert_domain_event_schema(root: Path, event_ref: str) -> Dict[str, Any]:
    event_path = root / event_ref
    assert event_path.exists(), event_ref
    payload = load_json(event_path)

    for field in REQUIRED_EVENT_FIELDS:
        assert str(payload.get(field) or "").strip(), field

    assert payload["contract_version"] == "0.1.0"
    assert payload["module"] in {"m1", "m3", "m4", "m5", "runtime-monitor"}
    assert payload["trigger_source"] in {"platform-hook", "domain-hook", "heartbeat", "cron"}
    assert payload["severity"] in {"info", "warning", "critical"}
    assert payload.get("asset_ref") or payload.get("target_product_id")
    return payload


def test_full_development_emits_domain_event(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("full-development-event", tmp_path)

    objective_context = case_dir / "objective_context.md"
    objective_context.write_text("# objective\n", encoding="utf-8")
    input_payload = case_dir / "input_payload.json"
    dump_json(input_payload, {"intent": "domain-event-regression"})

    runner_input = case_dir / "input.json"
    runner_output = case_dir / "output.json"
    dump_json(
        runner_input,
        {
            "objective_context_ref": str(objective_context.resolve()),
            "input_payload": str(input_payload.resolve()),
            "target_asset_type": "process",
            "lifecycle_target": "review",
            "superpower_ref": str((root / "docs/plans/SuperPower.md").resolve()),
        },
    )

    cmd = [
        sys.executable,
        "processes/meta/full-development/scripts/full_development_runner.py",
        "--input",
        str(runner_input),
        "--output",
        str(runner_output),
        "--evidence-dir",
        str(case_dir / "execution"),
        "--run-id",
        "TC-M5-EVENT-001",
    ]
    proc = run_cmd(cmd, root)
    assert proc.returncode == 0, proc.stderr

    output = load_json(runner_output)
    payload = assert_domain_event_schema(root, str(output.get("domain_event_ref") or ""))
    assert payload["event_name"] == "m3.implementation.completed"


def test_quality_gate_failure_emits_domain_event(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("quality-gate-event", tmp_path)

    runner_input = case_dir / "input.json"
    runner_output = case_dir / "output.json"
    dump_json(runner_input, {})

    cmd = [
        sys.executable,
        "processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py",
        "--input",
        str(runner_input),
        "--output",
        str(runner_output),
        "--evidence-dir",
        str(case_dir / "execution"),
        "--run-id",
        "TC-M5-EVENT-002",
    ]
    proc = run_cmd(cmd, root)
    assert proc.returncode == 2, proc.stderr

    output = load_json(runner_output)
    payload = assert_domain_event_schema(root, str(output.get("domain_event_ref") or ""))
    assert payload["event_name"] == "m1.gate.failed"


def test_lifecycle_review_success_emits_domain_event(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("lifecycle-event", tmp_path)

    gate_verdict = case_dir / "gate_verdict.json"
    target_asset = case_dir / "target_asset.json"
    runner_input = case_dir / "input.json"
    runner_output = case_dir / "output.json"

    dump_json(gate_verdict, {"gate_decision": "pass"})
    dump_json(
        target_asset,
        {
            "asset_id": "process:full-development",
            "lifecycle_status": "review",
        },
    )
    dump_json(
        runner_input,
        {
            "final_gate_verdict_ref": str(gate_verdict.resolve()),
            "target_asset_ref": str(target_asset.resolve()),
            "requested_transition": {"from_status": "review", "to_status": "active"},
        },
    )

    cmd = [
        sys.executable,
        "processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py",
        "--input",
        str(runner_input),
        "--output",
        str(runner_output),
        "--evidence-dir",
        str(case_dir / "execution"),
        "--run-id",
        "TC-M5-EVENT-003",
        "--registry-verify-cmd",
        "python3 -c \"print('registry verify bypass for test')\"",
    ]
    proc = run_cmd(cmd, root)
    assert proc.returncode == 0, proc.stderr

    output = load_json(runner_output)
    payload = assert_domain_event_schema(root, str(output.get("domain_event_ref") or ""))
    assert payload["event_name"] == "m4.lifecycle.transition.approved"
