#!/usr/bin/env python3
"""Run TC-GCC-001~003 for governed config-change runtime hardening."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
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


def parse_json_from_mixed_output(text: str) -> Any:
    decoder = json.JSONDecoder()
    fallback = None
    for idx, ch in enumerate(text):
        if ch not in "[{":
            continue
        try:
            value, end = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        remainder = text[idx + end :].strip()
        if not remainder:
            return value
        fallback = value
    if fallback is not None:
        return fallback

    for line in reversed(text.splitlines()):
        raw = line.strip()
        if not raw:
            continue
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            continue
    raise RuntimeError("no JSON found in command output")


def is_transient_gateway_failure(proc: subprocess.CompletedProcess[str]) -> bool:
    text = (proc.stdout + "\n" + proc.stderr).lower()
    markers = [
        "gateway closed",
        "abnormal closure",
        "econnrefused",
        "connection refused",
        "gateway call failed",
    ]
    return any(marker in text for marker in markers)


def load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_nested(payload: Dict[str, Any], dotted_path: str) -> Any:
    node: Any = payload
    for token in dotted_path.split("."):
        if not isinstance(node, dict) or token not in node:
            return None
        node = node[token]
    return node


def read_config_state(root: Path, profile: str | None) -> Tuple[str, Dict[str, Any]]:
    cmd = ["openclaw"]
    if profile:
        cmd.extend(["--profile", profile])
    cmd.extend(["gateway", "call", "config.get", "--params", "{}", "--json"])
    proc: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, 6):
        proc = run_cmd(cmd, root)
        if proc.returncode == 0:
            break
        if is_transient_gateway_failure(proc) and attempt < 5:
            time.sleep(float(attempt))
            continue
        raise RuntimeError(f"config.get failed: {proc.stderr.strip()}")
    if proc is None:
        raise RuntimeError("config.get failed before execution")
    payload = parse_json_from_mixed_output(proc.stdout)
    if not isinstance(payload, dict):
        raise RuntimeError("config.get payload must be object")
    hash_value = payload.get("hash")
    config_obj = payload.get("parsed") or payload.get("config")
    if not isinstance(hash_value, str) or not hash_value:
        raise RuntimeError("config.get hash missing")
    if not isinstance(config_obj, dict):
        raise RuntimeError("config.get parsed/config missing")
    return hash_value, config_obj


def append_case(cases: List[Dict[str, Any]], case_id: str, ok: bool, details: Dict[str, Any]) -> None:
    cases.append({"id": case_id, "status": "pass" if ok else "fail", "details": details})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TC-GCC-001~003")
    parser.add_argument(
        "--process-runner",
        default="processes/meta/governed-config-change/scripts/governed_config_change_runner.py",
        help="Repo-relative governed-config-change runner path",
    )
    parser.add_argument(
        "--updater-runner",
        default="skills/system/system-config-updater/scripts/system_config_updater_runner.py",
        help="Repo-relative system-config-updater runner path",
    )
    parser.add_argument(
        "--report",
        default="docs/design/modules/evidence/bpm-runtime/w2_tc_gcc_report.json",
        help="Repo-relative report output path",
    )
    parser.add_argument(
        "--evidence-root",
        default="docs/design/modules/evidence/bpm-runtime/w2_tc_gcc_cases",
        help="Repo-relative evidence root for case artifacts",
    )
    parser.add_argument(
        "--target-path",
        default="messages.groupChat.historyLimit",
        help="Config path used for live low-risk patch",
    )
    parser.add_argument(
        "--openclaw-profile",
        default="",
        help="Optional OpenClaw profile name",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    profile = args.openclaw_profile.strip() or None

    process_runner = (root / args.process_runner).resolve()
    updater_runner = (root / args.updater_runner).resolve()
    if not process_runner.exists():
        raise RuntimeError(f"process runner not found: {process_runner}")
    if not updater_runner.exists():
        raise RuntimeError(f"updater runner not found: {updater_runner}")

    evidence_root = (root / args.evidence_root).resolve()
    evidence_root.mkdir(parents=True, exist_ok=True)
    report_path = (root / args.report).resolve()

    cases: List[Dict[str, Any]] = []

    # TC-GCC-001
    tc1_dir = evidence_root / "TC-GCC-001"
    tc1_dir.mkdir(parents=True, exist_ok=True)
    tc1_input = tc1_dir / "input.json"
    tc1_output = tc1_dir / "process_output.json"
    tc1_evidence_rel = f"{args.evidence_root}/TC-GCC-001/evidence"

    before_hash_1, before_cfg_1 = read_config_state(root, profile)
    before_value_1 = get_nested(before_cfg_1, args.target_path)
    if not isinstance(before_value_1, int):
        raise RuntimeError(f"target value is not int at {args.target_path}: {before_value_1!r}")

    tc1_payload = {
        "objective_ref": "obj-governed-openclaw-config-change",
        "change_request": {
            "target_scope": {"path": args.target_path},
            "delta": 1,
        },
        "requester": "personal-assistant",
        "target_scope": {"path": args.target_path},
        "rollback_plan": {
            "mode": "restore_previous_value",
            "executable": True,
            "owner": "admin",
        },
        "evidence_refs": [
            "docs/architecture/openclaw_interface.md",
            "tests/m2-bpm-runtime/TC-GCC.md",
        ],
        "authorization": {
            "approved": True,
            "approved_by_role": "admin",
            "approval_id": "TC-GCC-001",
            "allowed_paths": [args.target_path],
        },
    }
    dump_json(tc1_input, tc1_payload)
    tc1_cmd = [
        sys.executable,
        str(process_runner),
        "--input",
        str(tc1_input),
        "--output",
        str(tc1_output),
        "--evidence-dir",
        tc1_evidence_rel,
    ]
    if profile:
        tc1_cmd.extend(["--openclaw-profile", profile])
    tc1_proc = run_cmd(tc1_cmd, root)
    tc1_details: Dict[str, Any] = {
        "return_code": tc1_proc.returncode,
        "stdout": tc1_proc.stdout.strip(),
        "stderr": tc1_proc.stderr.strip(),
    }
    tc1_ok = tc1_proc.returncode == 0 and tc1_output.exists()
    if tc1_ok:
        tc1_result = load_json(tc1_output)
        verify_path = root / tc1_evidence_rel / "verification_report.json"
        verify_payload = load_json(verify_path) if verify_path.exists() else {}
        after_hash_1, after_cfg_1 = read_config_state(root, profile)
        after_value_1 = get_nested(after_cfg_1, args.target_path)

        tc1_ok = (
            tc1_result.get("verdict") == "pass"
            and verify_payload.get("apply_value_match") is True
            and verify_payload.get("rollback_value_restored") is True
            and after_value_1 == before_value_1
            and isinstance(verify_payload.get("hash_after_rollback"), str)
            and after_hash_1 == verify_payload.get("hash_after_rollback")
        )
        tc1_details.update(
            {
                "verdict": tc1_result.get("verdict"),
                "hash_before": verify_payload.get("hash_before"),
                "hash_after_apply": verify_payload.get("hash_after_apply"),
                "hash_after_rollback": verify_payload.get("hash_after_rollback"),
                "value_before": verify_payload.get("value_before"),
                "value_after_apply": verify_payload.get("value_after_apply"),
                "value_after_rollback": verify_payload.get("value_after_rollback"),
                "verify_ref": str(verify_path.relative_to(root)),
            }
        )
    append_case(cases, "TC-GCC-001", tc1_ok, tc1_details)

    # TC-GCC-002
    tc2_dir = evidence_root / "TC-GCC-002"
    tc2_dir.mkdir(parents=True, exist_ok=True)
    tc2_input = tc2_dir / "input.json"
    tc2_output = tc2_dir / "updater_output.json"
    tc2_receipt = tc2_dir / "change_receipt.json"

    before_hash_2, before_cfg_2 = read_config_state(root, profile)
    before_value_2 = get_nested(before_cfg_2, args.target_path)
    if not isinstance(before_value_2, int):
        raise RuntimeError(f"target value is not int at {args.target_path}: {before_value_2!r}")
    stale_hash = ("0" if before_hash_2[0] != "0" else "1") + before_hash_2[1:]

    tc2_payload = {
        "base_hash": stale_hash,
        "patch_raw": json.dumps({"messages": {"groupChat": {"historyLimit": before_value_2 + 1}}}, ensure_ascii=False),
        "rollback_plan": {"mode": "restore_previous_value", "executable": True},
        "authorization": {
            "approved": True,
            "approved_by_role": "admin",
            "approval_id": "TC-GCC-002",
            "allowed_paths": [args.target_path],
        },
        "target_path": args.target_path,
    }
    dump_json(tc2_input, tc2_payload)
    tc2_cmd = [
        sys.executable,
        str(updater_runner),
        "--input",
        str(tc2_input),
        "--output",
        str(tc2_output),
        "--receipt",
        str(tc2_receipt),
    ]
    if profile:
        tc2_cmd.extend(["--openclaw-profile", profile])
    tc2_proc = run_cmd(tc2_cmd, root)
    after_hash_2, _ = read_config_state(root, profile)

    tc2_details = {
        "return_code": tc2_proc.returncode,
        "stdout": tc2_proc.stdout.strip(),
        "stderr": tc2_proc.stderr.strip(),
        "hash_before": before_hash_2,
        "hash_after": after_hash_2,
    }
    tc2_ok = tc2_proc.returncode == 2 and tc2_output.exists()
    if tc2_ok:
        tc2_result = load_json(tc2_output)
        tc2_ok = (
            tc2_result.get("execution_status") == "failed"
            and tc2_result.get("failure_code") == "base_hash_mismatch"
            and after_hash_2 == before_hash_2
        )
        tc2_details.update(
            {
                "execution_status": tc2_result.get("execution_status"),
                "failure_code": tc2_result.get("failure_code"),
                "receipt_ref": tc2_result.get("receipt_ref"),
            }
        )
    append_case(cases, "TC-GCC-002", tc2_ok, tc2_details)

    # TC-GCC-003
    tc3_dir = evidence_root / "TC-GCC-003"
    tc3_dir.mkdir(parents=True, exist_ok=True)
    tc3_input = tc3_dir / "input.json"
    tc3_output = tc3_dir / "process_output.json"
    tc3_evidence_rel = f"{args.evidence_root}/TC-GCC-003/evidence"

    before_hash_3, _ = read_config_state(root, profile)

    tc3_payload = {
        "objective_ref": "obj-governed-openclaw-config-change",
        "change_request": {
            "target_scope": {"path": args.target_path},
            "delta": 1,
        },
        "requester": "personal-assistant",
        "target_scope": {"path": args.target_path},
        "rollback_plan": {
            "mode": "restore_previous_value",
            "executable": True,
            "owner": "admin",
        },
        "evidence_refs": [],
        "authorization": {
            "approved": True,
            "approved_by_role": "admin",
            "approval_id": "TC-GCC-003",
            "allowed_paths": [args.target_path],
        },
    }
    dump_json(tc3_input, tc3_payload)
    tc3_cmd = [
        sys.executable,
        str(process_runner),
        "--input",
        str(tc3_input),
        "--output",
        str(tc3_output),
        "--evidence-dir",
        tc3_evidence_rel,
    ]
    if profile:
        tc3_cmd.extend(["--openclaw-profile", profile])
    tc3_proc = run_cmd(tc3_cmd, root)
    after_hash_3, _ = read_config_state(root, profile)
    tc3_gate_path = root / tc3_evidence_rel / "gate_result.json"

    tc3_details = {
        "return_code": tc3_proc.returncode,
        "stdout": tc3_proc.stdout.strip(),
        "stderr": tc3_proc.stderr.strip(),
        "gate_result_ref": str(tc3_gate_path.relative_to(root)) if tc3_gate_path.exists() else None,
        "hash_before": before_hash_3,
        "hash_after": after_hash_3,
    }
    tc3_ok = tc3_proc.returncode == 2 and tc3_output.exists() and tc3_gate_path.exists()
    if tc3_ok:
        tc3_result = load_json(tc3_output)
        tc3_gate = load_json(tc3_gate_path)
        tc3_ok = (
            tc3_result.get("verdict") == "deny"
            and tc3_gate.get("approval") == "deny"
            and after_hash_3 == before_hash_3
        )
        tc3_details.update(
            {
                "verdict": tc3_result.get("verdict"),
                "gate_approval": tc3_gate.get("approval"),
                "gate_reason": tc3_gate.get("reason"),
            }
        )
    append_case(cases, "TC-GCC-003", tc3_ok, tc3_details)

    passed = sum(1 for case in cases if case["status"] == "pass")
    failed = len(cases) - passed
    report = {
        "ts": now_iso(),
        "suite": "TC-GCC-001~003",
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "target_path": args.target_path,
        "evidence_root": args.evidence_root,
        "cases": cases,
    }
    dump_json(report_path, report)

    print(json.dumps(report, ensure_ascii=False))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
