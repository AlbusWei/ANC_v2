#!/usr/bin/env python3
"""Run TC-INS-001~005 for M2 BPM runtime hardening W1."""

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


def append_case(cases: List[Dict[str, Any]], case_id: str, ok: bool, details: Dict[str, Any]) -> None:
    cases.append({"id": case_id, "status": "pass" if ok else "fail", "details": details})


def main() -> int:
    parser = argparse.ArgumentParser(description="Run TC-INS-001~005")
    parser.add_argument(
        "--runner",
        default="skills/system/process-instance-manager/scripts/process_instance_runner.py",
        help="repo-relative runner path",
    )
    parser.add_argument(
        "--report",
        default="docs/design/modules/evidence/bpm-runtime/w1_tc_ins_report.json",
        help="repo-relative report output path",
    )
    parser.add_argument(
        "--sandbox-root",
        default="tmp/m2-bpm-runtime/tc-ins-sandbox",
        help="repo-relative sandbox root for TC1-4",
    )
    parser.add_argument(
        "--live-instance-root",
        default="agents/control/BPM/memory/process_instances",
        help="repo-relative live instance root for TC5",
    )
    parser.add_argument(
        "--migration-report",
        default="docs/design/modules/evidence/bpm-runtime/w1_migration_report.json",
        help="repo-relative migration report path",
    )
    parser.add_argument(
        "--replay-report",
        default="docs/design/modules/evidence/bpm-runtime/w1_replay_report.json",
        help="repo-relative replay report path",
    )
    parser.add_argument(
        "--run-live-migration",
        action="store_true",
        help="execute live migration/replay before TC5 assertions",
    )
    args = parser.parse_args()

    root = repo_root()
    runner = (root / args.runner).resolve()
    if not runner.exists():
        raise RuntimeError(f"runner not found: {runner}")

    report_path = (root / args.report).resolve()
    sandbox_root = (root / args.sandbox_root).resolve()
    sandbox_instances = sandbox_root / "instances"

    migration_report = (root / args.migration_report).resolve()
    replay_report = (root / args.replay_report).resolve()

    if sandbox_root.exists():
        shutil.rmtree(sandbox_root)
    sandbox_instances.mkdir(parents=True, exist_ok=True)

    cases: List[Dict[str, Any]] = []

    # TC-INS-001
    tc1_out = sandbox_root / "tc1_start.json"
    cmd_tc1 = [
        sys.executable,
        str(runner),
        "start",
        "--process-id",
        "development-process",
        "--phase-id",
        "p1",
        "--instance-root",
        str(sandbox_instances),
        "--instance-id",
        "tc-ins-root",
        "--stack-depth",
        "0",
        "--output",
        str(tc1_out),
    ]
    run1 = run_cmd(cmd_tc1, root)
    tc1_ok = run1.returncode == 0
    tc1_details: Dict[str, Any] = {
        "return_code": run1.returncode,
        "stderr": run1.stderr.strip(),
    }
    root_context: Dict[str, Any] = {}
    root_binding: Dict[str, Any] = {}
    if tc1_ok and tc1_out.exists():
        start_payload = load_json(tc1_out)
        context_path = root / start_payload["context_ref"]
        binding_path = root / start_payload["session_binding_ref"]
        dispatch_context_ref = str(start_payload.get("dispatch_context_ref") or "")
        task_dispatch_ref = str(start_payload.get("task_dispatch_ref") or "")
        dispatch_context_path = root / dispatch_context_ref if dispatch_context_ref else Path("/non-existent")
        task_dispatch_path = root / task_dispatch_ref if task_dispatch_ref else Path("/non-existent")
        root_context = load_json(context_path)
        root_binding = load_json(binding_path)

        required = [
            "session_binding",
            "lineage_ref",
            "stack_depth",
            "process_version",
            "process_level",
        ]
        missing = [key for key in required if key not in root_context]
        phase_session_ok = bool(root_context.get("phase_results") and root_context["phase_results"][0].get("session_id"))
        binding_match = root_context.get("session_binding") == root_binding
        dispatch_refs_ok = dispatch_context_path.exists() and task_dispatch_path.exists()
        tc1_ok = tc1_ok and not missing and phase_session_ok and binding_match and dispatch_refs_ok
        tc1_details.update(
            {
                "missing_fields": missing,
                "phase_session_ok": phase_session_ok,
                "binding_match": binding_match,
                "dispatch_refs_ok": dispatch_refs_ok,
            }
        )
    append_case(cases, "TC-INS-001", tc1_ok, tc1_details)

    # TC-INS-002
    tc2_out = sandbox_root / "tc2_start_child.json"
    cmd_tc2 = [
        sys.executable,
        str(runner),
        "start",
        "--process-id",
        "development-process",
        "--phase-id",
        "p2",
        "--instance-root",
        str(sandbox_instances),
        "--instance-id",
        "tc-ins-child",
        "--parent-instance-id",
        "tc-ins-root",
        "--output",
        str(tc2_out),
    ]
    run2 = run_cmd(cmd_tc2, root)
    tc2_ok = run2.returncode == 0
    tc2_details: Dict[str, Any] = {
        "return_code": run2.returncode,
        "stderr": run2.stderr.strip(),
    }
    child_context: Dict[str, Any] = {}
    if tc2_ok and tc2_out.exists() and root_context and root_binding:
        child_payload = load_json(tc2_out)
        child_context = load_json(root / child_payload["context_ref"])
        child_binding = load_json(root / child_payload["session_binding_ref"])

        depth_ok = child_context.get("stack_depth") == int(root_context.get("stack_depth", -1)) + 1
        parent_link_ok = child_binding.get("parent_session_id") == root_binding.get("session_id")
        no_reuse = child_binding.get("session_id") != root_binding.get("session_id")
        tc2_ok = tc2_ok and depth_ok and parent_link_ok and no_reuse
        tc2_details.update(
            {
                "depth_ok": depth_ok,
                "parent_link_ok": parent_link_ok,
                "no_reuse": no_reuse,
            }
        )
    append_case(cases, "TC-INS-002", tc2_ok, tc2_details)

    # TC-INS-003
    tc3_out = sandbox_root / "tc3_start_bad_child.json"
    parent_session = str(root_binding.get("session_id") or "")
    cmd_tc3 = [
        sys.executable,
        str(runner),
        "start",
        "--process-id",
        "development-process",
        "--phase-id",
        "p2",
        "--instance-root",
        str(sandbox_instances),
        "--instance-id",
        "tc-ins-bad-child",
        "--parent-instance-id",
        "tc-ins-root",
        "--session-id",
        parent_session,
        "--output",
        str(tc3_out),
    ]
    run3 = run_cmd(cmd_tc3, root)
    tc3_ok = run3.returncode != 0
    tc3_details = {
        "return_code": run3.returncode,
        "stderr": run3.stderr.strip(),
    }
    append_case(cases, "TC-INS-003", tc3_ok, tc3_details)

    # TC-INS-004
    tc4_ok = False
    tc4_details: Dict[str, Any] = {}
    if tc1_out.exists():
        start_payload = load_json(tc1_out)
        dispatch = start_payload.get("dispatch", {})
        command = dispatch.get("command", [])
        has_flag = isinstance(command, list) and "--session-id" in command
        matches = False
        if has_flag:
            idx = command.index("--session-id")
            if idx + 1 < len(command):
                matches = command[idx + 1] == root_binding.get("session_id")
        tc4_ok = has_flag and matches
        tc4_details = {
            "has_session_flag": has_flag,
            "session_id_matches": matches,
        }
    append_case(cases, "TC-INS-004", tc4_ok, tc4_details)

    # TC-INS-005
    if args.run_live_migration:
        cmd_migrate = [
            sys.executable,
            str(runner),
            "migrate",
            "--instance-root",
            str((root / args.live_instance_root).resolve()),
            "--output",
            str(migration_report),
        ]
        run_migrate = run_cmd(cmd_migrate, root)

        cmd_replay = [
            sys.executable,
            str(runner),
            "replay",
            "--instance-root",
            str((root / args.live_instance_root).resolve()),
            "--output",
            str(replay_report),
        ]
        run_replay = run_cmd(cmd_replay, root)
    else:
        run_migrate = None
        run_replay = None

    tc5_ok = migration_report.exists() and replay_report.exists()
    tc5_details: Dict[str, Any] = {
        "migration_report": str(migration_report),
        "replay_report": str(replay_report),
    }
    if run_migrate is not None:
        tc5_details["migration_return_code"] = run_migrate.returncode
        tc5_details["migration_stderr"] = run_migrate.stderr.strip()
    if run_replay is not None:
        tc5_details["replay_return_code"] = run_replay.returncode
        tc5_details["replay_stderr"] = run_replay.stderr.strip()

    if tc5_ok:
        migration_payload = load_json(migration_report)
        replay_payload = load_json(replay_report)
        migration_ok = int(migration_payload.get("failed", 1)) == 0
        replay_ok = int(replay_payload.get("failed", 1)) == 0
        tc5_ok = tc5_ok and migration_ok and replay_ok
        tc5_details.update(
            {
                "migration_total": migration_payload.get("total"),
                "migration_failed": migration_payload.get("failed"),
                "replay_total": replay_payload.get("total"),
                "replay_failed": replay_payload.get("failed"),
            }
        )
    append_case(cases, "TC-INS-005", tc5_ok, tc5_details)

    passed = sum(1 for item in cases if item["status"] == "pass")
    failed = len(cases) - passed
    report = {
        "ts": now_iso(),
        "suite": "TC-INS-001~005",
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "cases": cases,
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
