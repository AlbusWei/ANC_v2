#!/usr/bin/env python3
"""Run TC-HOTFIX-PROC-001 and TC-REFACTOR-PROC-001 for process collaboration runtime."""

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


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def check_ref_exists(root: Path, ref: str) -> bool:
    if not ref:
        return False
    path = Path(ref)
    if not path.is_absolute():
        path = (root / ref).resolve()
    return path.exists()


def collect_dispatch_checks(phase_trace: List[Dict[str, Any]]) -> Dict[str, Any]:
    dispatch_checks: List[Dict[str, Any]] = []
    sessions: Dict[str, str] = {}
    all_ok = True

    for item in phase_trace:
        phase = str(item.get("phase") or "")
        dispatch = item.get("dispatch") if isinstance(item.get("dispatch"), dict) else {}
        session_id = str(dispatch.get("session_id") or "")
        actual_session_id = str(dispatch.get("actual_session_id") or "")
        phase_ok = (
            bool(dispatch.get("enabled"))
            and bool(dispatch.get("executed"))
            and dispatch.get("return_code") == 0
            and bool(session_id)
            and bool(actual_session_id)
            and session_id == actual_session_id
        )
        dispatch_checks.append(
            {
                "phase": phase,
                "ok": phase_ok,
                "session_id": session_id,
                "actual_session_id": actual_session_id,
            }
        )
        sessions[phase] = session_id
        all_ok = all_ok and phase_ok

    return {
        "all_ok": all_ok,
        "dispatch_checks": dispatch_checks,
        "sessions": sessions,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TC-HOTFIX-PROC-001 and TC-REFACTOR-PROC-001")
    parser.add_argument(
        "--hotfix-runner",
        default="processes/meta/hotfix/scripts/hotfix_runner.py",
        help="Repo-relative hotfix runner path",
    )
    parser.add_argument(
        "--refactor-runner",
        default="processes/meta/refactor/scripts/refactor_runner.py",
        help="Repo-relative refactor runner path",
    )
    parser.add_argument(
        "--report",
        default="runtime_data/execution/evidence/bpm-runtime/w3d_tc_hotfix_refactor_proc_report.json",
        help="Repo-relative report output path",
    )
    parser.add_argument(
        "--evidence-root",
        default="runtime_data/execution/evidence/bpm-runtime/w3d_hotfix_refactor_cases",
        help="Repo-relative evidence root",
    )
    return parser.parse_args()


def run_hotfix_case(root: Path, runner: Path, case_dir: Path) -> Dict[str, Any]:
    case_id = "TC-HOTFIX-PROC-001"

    incident_context = case_dir / "incident_context.md"
    incident_context.write_text(
        "# Hotfix Incident\n\n- incident: 线上故障需快速收敛修复范围。\n",
        encoding="utf-8",
    )
    target_asset = case_dir / "target_asset.md"
    target_asset.write_text(
        "# Target Asset\n\n- asset: process:hotfix\n",
        encoding="utf-8",
    )

    runner_input = case_dir / "runner_input.json"
    runner_output = case_dir / "runner_output.json"
    dump_json(
        runner_input,
        {
            "incident_context_ref": to_rel(incident_context, root),
            "target_asset_ref": to_rel(target_asset, root),
            "lifecycle_target": "review",
        },
    )

    cmd = [
        sys.executable,
        str(runner),
        "--input",
        str(runner_input),
        "--output",
        str(runner_output),
        "--evidence-dir",
        str((case_dir / "execution").relative_to(root)),
        "--run-id",
        case_id,
        "--enable-phase-dispatch",
        "--dispatch-openclaw",
        "--reset-openclaw-session",
        "--strict-session-match",
    ]
    proc = run_cmd(cmd, root)
    (case_dir / "runner.stdout.log").write_text(proc.stdout, encoding="utf-8")
    (case_dir / "runner.stderr.log").write_text(proc.stderr, encoding="utf-8")

    details: Dict[str, Any] = {
        "return_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }

    ok = proc.returncode == 0 and runner_output.exists()
    if ok:
        output = load_json(runner_output)
        runtime_trace_ref = str(output.get("runtime_trace_ref") or "")
        runtime_trace = load_json((root / runtime_trace_ref).resolve())
        phase_trace = runtime_trace.get("phase_trace", [])

        required_outputs = [
            "final_gate_verdict_ref",
            "lifecycle_transition_ref",
            "registry_sync_ref",
            "release_package_ref",
            "rollback_bundle_ref",
        ]

        dispatch_result = collect_dispatch_checks(phase_trace)
        sessions = dispatch_result["sessions"]
        actor_isolation_ok = (
            sessions.get("p1")
            and sessions.get("p2")
            and sessions.get("p1") != sessions.get("p2")
            and sessions.get("p3")
            and sessions.get("p5")
            and sessions.get("p3") != sessions.get("p5")
            and sessions.get("p6")
            and sessions.get("p7")
            and sessions.get("p6") != sessions.get("p7")
        )

        output_refs_ok = all(check_ref_exists(root, str(output.get(key) or "")) for key in required_outputs)
        phase_count_ok = len(phase_trace) == 7
        collaboration_mode_ok = str(output.get("collaboration_mode") or "") == "phase-isolated-session"

        ok = (
            output.get("status") == "ok"
            and phase_count_ok
            and collaboration_mode_ok
            and dispatch_result["all_ok"]
            and actor_isolation_ok
            and output_refs_ok
        )

        details.update(
            {
                "runtime_trace_ref": runtime_trace_ref,
                "phase_count": len(phase_trace),
                "dispatch_checks": dispatch_result["dispatch_checks"],
                "actor_isolation_ok": actor_isolation_ok,
                "output_refs_ok": output_refs_ok,
                "collaboration_mode": output.get("collaboration_mode"),
            }
        )

    return {
        "id": case_id,
        "status": "pass" if ok else "fail",
        "details": details,
    }


def run_refactor_case(root: Path, runner: Path, case_dir: Path) -> Dict[str, Any]:
    case_id = "TC-REFACTOR-PROC-001"

    objective_context = case_dir / "objective_context.md"
    objective_context.write_text(
        "# Refactor Objective\n\n- objective: 清理结构耦合并保持行为一致。\n",
        encoding="utf-8",
    )
    tech_debt = case_dir / "tech_debt.md"
    tech_debt.write_text(
        "# Tech Debt\n\n- debt: 模块边界混杂，影响可维护性。\n",
        encoding="utf-8",
    )
    target_asset = case_dir / "target_asset.md"
    target_asset.write_text(
        "# Target Asset\n\n- asset: process:refactor\n",
        encoding="utf-8",
    )

    runner_input = case_dir / "runner_input.json"
    runner_output = case_dir / "runner_output.json"
    dump_json(
        runner_input,
        {
            "objective_context_ref": to_rel(objective_context, root),
            "tech_debt_ref": to_rel(tech_debt, root),
            "target_asset_ref": to_rel(target_asset, root),
            "lifecycle_target": "review",
        },
    )

    cmd = [
        sys.executable,
        str(runner),
        "--input",
        str(runner_input),
        "--output",
        str(runner_output),
        "--evidence-dir",
        str((case_dir / "execution").relative_to(root)),
        "--run-id",
        case_id,
        "--enable-phase-dispatch",
        "--dispatch-openclaw",
        "--reset-openclaw-session",
        "--strict-session-match",
    ]
    proc = run_cmd(cmd, root)
    (case_dir / "runner.stdout.log").write_text(proc.stdout, encoding="utf-8")
    (case_dir / "runner.stderr.log").write_text(proc.stderr, encoding="utf-8")

    details: Dict[str, Any] = {
        "return_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }

    ok = proc.returncode == 0 and runner_output.exists()
    if ok:
        output = load_json(runner_output)
        runtime_trace_ref = str(output.get("runtime_trace_ref") or "")
        runtime_trace = load_json((root / runtime_trace_ref).resolve())
        phase_trace = runtime_trace.get("phase_trace", [])

        required_outputs = [
            "final_gate_verdict_ref",
            "lifecycle_transition_ref",
            "registry_sync_ref",
        ]

        dispatch_result = collect_dispatch_checks(phase_trace)
        sessions = dispatch_result["sessions"]
        actor_isolation_ok = (
            sessions.get("p1")
            and sessions.get("p2")
            and sessions.get("p1") != sessions.get("p2")
            and sessions.get("p3")
            and sessions.get("p5")
            and sessions.get("p3") != sessions.get("p5")
        )

        output_refs_ok = all(check_ref_exists(root, str(output.get(key) or "")) for key in required_outputs)
        phase_count_ok = len(phase_trace) == 6
        collaboration_mode_ok = str(output.get("collaboration_mode") or "") == "phase-isolated-session"

        ok = (
            output.get("status") == "ok"
            and phase_count_ok
            and collaboration_mode_ok
            and dispatch_result["all_ok"]
            and actor_isolation_ok
            and output_refs_ok
        )

        details.update(
            {
                "runtime_trace_ref": runtime_trace_ref,
                "phase_count": len(phase_trace),
                "dispatch_checks": dispatch_result["dispatch_checks"],
                "actor_isolation_ok": actor_isolation_ok,
                "output_refs_ok": output_refs_ok,
                "collaboration_mode": output.get("collaboration_mode"),
            }
        )

    return {
        "id": case_id,
        "status": "pass" if ok else "fail",
        "details": details,
    }


def main() -> int:
    args = parse_args()
    root = repo_root()

    hotfix_runner = (root / args.hotfix_runner).resolve()
    refactor_runner = (root / args.refactor_runner).resolve()
    report_path = (root / args.report).resolve()
    evidence_root = (root / args.evidence_root).resolve()

    if not hotfix_runner.exists():
        raise RuntimeError(f"hotfix runner not found: {hotfix_runner}")
    if not refactor_runner.exists():
        raise RuntimeError(f"refactor runner not found: {refactor_runner}")

    if evidence_root.exists():
        shutil.rmtree(evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=True)

    hotfix_case_dir = evidence_root / "TC-HOTFIX-PROC-001"
    hotfix_case_dir.mkdir(parents=True, exist_ok=True)

    refactor_case_dir = evidence_root / "TC-REFACTOR-PROC-001"
    refactor_case_dir.mkdir(parents=True, exist_ok=True)

    cases = [
        run_hotfix_case(root, hotfix_runner, hotfix_case_dir),
        run_refactor_case(root, refactor_runner, refactor_case_dir),
    ]

    passed = sum(1 for case in cases if case["status"] == "pass")
    total = len(cases)

    report = {
        "ts": now_iso(),
        "suite": "TC-HOTFIX-REFACTOR-PROC",
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "evidence_root": to_rel(evidence_root, root),
        "cases": cases,
    }
    dump_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if passed == total else 2


if __name__ == "__main__":
    raise SystemExit(main())
