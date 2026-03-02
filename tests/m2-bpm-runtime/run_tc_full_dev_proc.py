#!/usr/bin/env python3
"""Run TC-FULL-DEV-PROC-001 for full-development collaboration skeleton."""

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TC-FULL-DEV-PROC-001")
    parser.add_argument(
        "--runner",
        default="processes/meta/full-development/scripts/full_development_runner.py",
        help="Repo-relative full-development runner path",
    )
    parser.add_argument(
        "--report",
        default="runtime_data/execution/evidence/bpm-runtime/w3c_tc_full_dev_proc_report.json",
        help="Repo-relative report output path",
    )
    parser.add_argument(
        "--evidence-root",
        default="runtime_data/execution/evidence/bpm-runtime/w3c_full_development_cases",
        help="Repo-relative evidence root",
    )
    parser.add_argument(
        "--superpower-ref",
        default="docs/plans/SuperPower.md",
        help="Repo-relative superpower reference document",
    )
    return parser.parse_args()


def check_ref_exists(root: Path, ref: str) -> bool:
    if not ref:
        return False
    path = Path(ref)
    if not path.is_absolute():
        path = (root / ref).resolve()
    return path.exists()


def main() -> int:
    args = parse_args()
    root = repo_root()

    runner = (root / args.runner).resolve()
    if not runner.exists():
        raise RuntimeError(f"runner not found: {runner}")
    superpower_path = (root / args.superpower_ref).resolve()
    if not superpower_path.exists():
        raise RuntimeError(f"superpower ref not found: {superpower_path}")
    superpower_ref = to_rel(superpower_path, root)

    report_path = (root / args.report).resolve()
    evidence_root = (root / args.evidence_root).resolve()
    if evidence_root.exists():
        shutil.rmtree(evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=True)

    case_id = "TC-FULL-DEV-PROC-001"
    case_dir = evidence_root / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    objective_context = case_dir / "objective_context.md"
    objective_context.write_text(
        "# 目标上下文\n\n- 目标：验证 full-development 在真实 openclaw 分发下可运行。\n",
        encoding="utf-8",
    )
    input_payload = case_dir / "input_payload.json"
    dump_json(
        input_payload,
        {
            "target_asset_id": "process:full-development",
            "change_ref": "docs/plans/SuperPower.md",
            "intent": "run-collaboration-skeleton",
        },
    )

    runner_input = case_dir / "runner_input.json"
    runner_output = case_dir / "runner_output.json"
    dump_json(
        runner_input,
        {
            "objective_context_ref": to_rel(objective_context, root),
            "input_payload": to_rel(input_payload, root),
            "target_asset_type": "process",
            "lifecycle_target": "review",
            "superpower_ref": superpower_ref,
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
        "TC-FULL-DEV-PROC-001",
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
            "improvement_plan_ref",
            "retro_report_ref",
        ]

        dispatch_checks = []
        session_by_phase: Dict[str, str] = {}
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
            dispatch_checks.append({"phase": phase, "ok": phase_ok, "session_id": session_id})
            session_by_phase[phase] = session_id

        actor_isolation_ok = (
            session_by_phase.get("p1")
            and session_by_phase.get("p2")
            and session_by_phase.get("p8")
            and len({session_by_phase.get("p1"), session_by_phase.get("p2"), session_by_phase.get("p8")}) == 3
            and session_by_phase.get("p3")
            and session_by_phase.get("p5")
            and session_by_phase.get("p3") != session_by_phase.get("p5")
            and session_by_phase.get("p6")
            and session_by_phase.get("p7")
            and session_by_phase.get("p6") != session_by_phase.get("p7")
        )

        output_refs_ok = all(check_ref_exists(root, str(output.get(key) or "")) for key in required_outputs)
        phase_count_ok = len(phase_trace) == 8
        collaboration_mode_ok = str(output.get("collaboration_mode") or "") == "phase-isolated-session"

        ok = (
            output.get("status") == "ok"
            and phase_count_ok
            and collaboration_mode_ok
            and all(item["ok"] for item in dispatch_checks)
            and actor_isolation_ok
            and output_refs_ok
        )

        details.update(
            {
                "runtime_trace_ref": runtime_trace_ref,
                "phase_count": len(phase_trace),
                "dispatch_checks": dispatch_checks,
                "actor_isolation_ok": actor_isolation_ok,
                "output_refs_ok": output_refs_ok,
                "collaboration_mode": output.get("collaboration_mode"),
            }
        )

    report = {
        "ts": now_iso(),
        "suite": "TC-FULL-DEV-PROC-001",
        "total": 1,
        "passed": 1 if ok else 0,
        "failed": 0 if ok else 1,
        "evidence_root": to_rel(evidence_root, root),
        "cases": [
            {
                "id": case_id,
                "status": "pass" if ok else "fail",
                "details": details,
            }
        ],
    }
    dump_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
