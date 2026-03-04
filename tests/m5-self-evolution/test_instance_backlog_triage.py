#!/usr/bin/env python3
"""M5 运行止血：实例积压 triage 工具回归测试。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict


ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def now_iso(delta_seconds: int = 0) -> str:
    ts = datetime.now(timezone.utc) + timedelta(seconds=delta_seconds)
    return ts.replace(microsecond=0).strftime(ISO_FMT)


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


def write_instance(
    *,
    root: Path,
    instance_id: str,
    status: str,
    phase: str,
    updated_at: str,
    phase_results: Any | None = None,
) -> Path:
    context = {
        "instance_id": instance_id,
        "status": status,
        "current_phase": phase,
        "updated_at": updated_at,
        "created_at": updated_at,
        "phase_results": phase_results
        if phase_results is not None
        else [
            {
                "phase_id": phase,
                "status": "running",
                "actor": "architect",
                "session_id": f"sess-{instance_id[-6:]}",
                "input_ref": "runtime_data/mock/input.json",
                "output_ref": "",
                "started_at": updated_at,
                "completed_at": "",
            }
        ],
    }
    instance_dir = root / instance_id
    dump_json(instance_dir / "context.json", context)
    return instance_dir / "context.json"


def write_dispatch_output(*, case_dir: Path, bucket: str, instance_id: str, executed: bool) -> Path:
    path = case_dir / "runtime_data" / "execution" / "evidence" / "m5-self-evolution" / "hook-bridge" / bucket / "p3_dispatch_output.json"
    dump_json(
        path,
        {
            "status": "ok",
            "instance_id": instance_id,
            "dispatch": {
                "executed": executed,
            },
        },
    )
    return path


def build_script_cmd(
    *,
    root: Path,
    pool_a: Path,
    pool_b: Path,
    report: Path,
    touched: Path,
    dispatch_glob: str,
    snapshot_only: bool,
    age_threshold_seconds: int = 3600,
    target_status: str = "archived",
) -> list[str]:
    cmd = [
        sys.executable,
        "tools/evolution/instance_backlog_triage.py",
        "--instance-root",
        str(pool_a),
        "--instance-root",
        str(pool_b),
        "--dispatch-glob",
        dispatch_glob,
        "--age-threshold-seconds",
        str(age_threshold_seconds),
        "--target-status",
        target_status,
        "--report",
        str(report),
        "--touched-output",
        str(touched),
    ]
    if snapshot_only:
        cmd.append("--snapshot-only")
    return cmd


def test_snapshot_only_outputs_pool_and_phase_baseline(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("triage-snapshot", tmp_path)

    pool_a = case_dir / "pool-a"
    pool_b = case_dir / "pool-b"
    report = case_dir / "report.json"
    touched = case_dir / "touched.json"

    write_instance(root=pool_a, instance_id="run-a-001", status="running", phase="p1", updated_at=now_iso(-7200))
    write_instance(root=pool_a, instance_id="run-a-002", status="running", phase="p2", updated_at=now_iso(-120))
    write_instance(root=pool_b, instance_id="run-b-001", status="failed", phase="p1", updated_at=now_iso(-3600))

    cmd = build_script_cmd(
        root=root,
        pool_a=pool_a,
        pool_b=pool_b,
        report=report,
        touched=touched,
        dispatch_glob=str(case_dir / "runtime_data" / "execution" / "evidence" / "m5-self-evolution" / "hook-bridge" / "**" / "p3_dispatch_output.json"),
        snapshot_only=True,
    )
    proc = run_cmd(cmd, root)

    assert proc.returncode == 0, proc.stderr
    payload = load_json(report)
    before = payload.get("baseline_before")
    assert isinstance(before, dict)
    assert before.get("total_instances") == 3

    pool_summaries = before.get("pools")
    assert isinstance(pool_summaries, list) and len(pool_summaries) == 2

    running_phases = before.get("running_phase_distribution")
    assert isinstance(running_phases, dict)
    assert running_phases.get("p1") == 1
    assert running_phases.get("p2") == 1

    assert payload.get("snapshot_only") is True
    touched_payload = load_json(touched)
    assert touched_payload.get("touched_count") == 0


def test_triage_only_touches_stale_running_p1_with_dispatch_false(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("triage-apply", tmp_path)

    pool_a = case_dir / "pool-a"
    pool_b = case_dir / "pool-b"
    report = case_dir / "report.json"
    touched = case_dir / "touched.json"

    stale_false_id = "run-stale-false-001"
    stale_true_id = "run-stale-true-001"
    fresh_false_id = "run-fresh-false-001"

    stale_ts = now_iso(-7200)
    fresh_ts = now_iso(-120)

    stale_false_ctx = write_instance(root=pool_a, instance_id=stale_false_id, status="running", phase="p1", updated_at=stale_ts)
    stale_true_ctx = write_instance(root=pool_a, instance_id=stale_true_id, status="running", phase="p1", updated_at=stale_ts)
    fresh_false_ctx = write_instance(root=pool_b, instance_id=fresh_false_id, status="running", phase="p1", updated_at=fresh_ts)

    write_dispatch_output(case_dir=case_dir, bucket="bucket-a", instance_id=stale_false_id, executed=False)
    write_dispatch_output(case_dir=case_dir, bucket="bucket-b", instance_id=stale_true_id, executed=True)
    write_dispatch_output(case_dir=case_dir, bucket="bucket-c", instance_id=fresh_false_id, executed=False)

    cmd = build_script_cmd(
        root=root,
        pool_a=pool_a,
        pool_b=pool_b,
        report=report,
        touched=touched,
        dispatch_glob=str(case_dir / "runtime_data" / "execution" / "evidence" / "m5-self-evolution" / "hook-bridge" / "**" / "p3_dispatch_output.json"),
        snapshot_only=False,
        age_threshold_seconds=3600,
        target_status="archived",
    )
    proc = run_cmd(cmd, root)

    assert proc.returncode == 0, proc.stderr

    stale_false_payload = load_json(stale_false_ctx)
    stale_true_payload = load_json(stale_true_ctx)
    fresh_false_payload = load_json(fresh_false_ctx)

    assert stale_false_payload.get("status") == "archived"
    phase_results = stale_false_payload.get("phase_results")
    assert isinstance(phase_results, list) and phase_results
    last_phase = phase_results[-1]
    assert last_phase.get("status") == "failed"
    assert isinstance(last_phase.get("completed_at"), str) and last_phase.get("completed_at")

    assert stale_true_payload.get("status") == "running"
    assert fresh_false_payload.get("status") == "running"

    report_payload = load_json(report)
    assert report_payload.get("candidate_count") == 1
    assert report_payload.get("touched_count") == 1

    touched_payload = load_json(touched)
    assert touched_payload.get("touched_count") == 1
    items = touched_payload.get("items")
    assert isinstance(items, list) and len(items) == 1
    assert items[0].get("instance_id") == stale_false_id


def test_triage_fail_closed_when_candidate_context_invalid(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("triage-fail-closed", tmp_path)

    pool_a = case_dir / "pool-a"
    pool_b = case_dir / "pool-b"
    report = case_dir / "report.json"
    touched = case_dir / "touched.json"

    instance_id = "run-invalid-001"
    original_ctx = write_instance(
        root=pool_a,
        instance_id=instance_id,
        status="running",
        phase="p1",
        updated_at=now_iso(-7200),
        phase_results="invalid",
    )

    write_dispatch_output(case_dir=case_dir, bucket="bucket-a", instance_id=instance_id, executed=False)

    cmd = build_script_cmd(
        root=root,
        pool_a=pool_a,
        pool_b=pool_b,
        report=report,
        touched=touched,
        dispatch_glob=str(case_dir / "runtime_data" / "execution" / "evidence" / "m5-self-evolution" / "hook-bridge" / "**" / "p3_dispatch_output.json"),
        snapshot_only=False,
        age_threshold_seconds=3600,
    )
    proc = run_cmd(cmd, root)

    assert proc.returncode == 2

    ctx_after = load_json(original_ctx)
    assert ctx_after.get("status") == "running"

    report_payload = load_json(report)
    assert report_payload.get("status") == "failed"
    assert str(report_payload.get("reason") or "").startswith("invalid_candidate_context")

    touched_payload = load_json(touched)
    assert touched_payload.get("touched_count") == 0
