#!/usr/bin/env python3
"""Executable runner for governed-config-change process."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


class GovernedConfigChangeError(RuntimeError):
    """Unexpected process runner failure."""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_id_now() -> str:
    return datetime.now(timezone.utc).strftime("gcc-%Y%m%dT%H%M%SZ")


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise GovernedConfigChangeError("not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def run_cmd(cmd: List[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(root), check=False, capture_output=True, text=True)


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
    raise GovernedConfigChangeError("no JSON payload found in command output")


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
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GovernedConfigChangeError(f"input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GovernedConfigChangeError(f"input JSON invalid: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise GovernedConfigChangeError("input payload must be object")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


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
        raise GovernedConfigChangeError(
            "config.get failed\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )
    if proc is None:
        raise GovernedConfigChangeError("config.get failed before execution")
    payload = parse_json_from_mixed_output(proc.stdout)
    if not isinstance(payload, dict):
        raise GovernedConfigChangeError("config.get output must be object")
    hash_value = payload.get("hash")
    config_obj = payload.get("parsed") or payload.get("config")
    if not isinstance(hash_value, str) or not hash_value.strip():
        raise GovernedConfigChangeError("config.get output missing hash")
    if not isinstance(config_obj, dict):
        raise GovernedConfigChangeError("config.get output missing parsed/config object")
    return hash_value, config_obj


def normalize_target_path(payload: Dict[str, Any]) -> str:
    top_scope = payload.get("target_scope")
    change_request = payload.get("change_request")
    candidates: List[str] = []

    if isinstance(top_scope, str) and top_scope.strip():
        candidates.append(top_scope.strip())
    elif isinstance(top_scope, dict):
        path = top_scope.get("path")
        if isinstance(path, str) and path.strip():
            candidates.append(path.strip())

    if isinstance(change_request, dict):
        scope = change_request.get("target_scope")
        if isinstance(scope, str) and scope.strip():
            candidates.append(scope.strip())
        elif isinstance(scope, dict):
            path = scope.get("path")
            if isinstance(path, str) and path.strip():
                candidates.append(path.strip())

    unique = sorted(set(candidates))
    if not unique:
        raise GovernedConfigChangeError("target_scope.path is required")
    if len(unique) > 1:
        raise GovernedConfigChangeError(f"conflicting target scopes: {unique}")
    return unique[0]


def validate_authorization(authorization: Any, target_path: str) -> Tuple[bool, str]:
    if not isinstance(authorization, dict):
        return False, "authorization missing or invalid"
    if authorization.get("approved") is not True:
        return False, "authorization.approved must be true"
    role = authorization.get("approved_by_role")
    if not isinstance(role, str) or not role.strip():
        return False, "authorization.approved_by_role is required"
    if role not in {"admin", "human"}:
        return False, f"insufficient authorization role: {role}"
    scopes = authorization.get("allowed_paths")
    if scopes is not None:
        if not isinstance(scopes, list) or not all(isinstance(item, str) and item.strip() for item in scopes):
            return False, "authorization.allowed_paths must be string list when provided"
        if target_path not in scopes:
            return False, f"authorization.allowed_paths does not include target path: {target_path}"
    return True, "authorized"


def invoke_runner(
    root: Path,
    cmd: List[str],
    output_path: Path | None = None,
) -> Tuple[int, Dict[str, Any]]:
    proc = run_cmd(cmd, root)
    payload: Dict[str, Any] = {}
    if output_path is not None and output_path.exists():
        try:
            payload = load_json(output_path)
        except GovernedConfigChangeError:
            payload = {}
    return proc.returncode, payload


def finalize(
    root: Path,
    output_path: Path,
    final_payload: Dict[str, Any],
    exit_code: int,
) -> int:
    dump_json(output_path, final_payload)
    print(to_rel(output_path, root))
    return exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run governed-config-change process")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--evidence-dir",
        default=None,
        help="Evidence directory (repo-relative). Default docs/design/modules/evidence/bpm-runtime/<run_id>",
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

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = root / input_path
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path

    payload = load_json(input_path)
    required = ["objective_ref", "change_request", "requester", "target_scope", "rollback_plan"]
    missing = [key for key in required if key not in payload]
    if missing:
        raise GovernedConfigChangeError(f"missing required input fields: {', '.join(missing)}")

    target_path = normalize_target_path(payload)
    if target_path != "messages.groupChat.historyLimit":
        raise GovernedConfigChangeError(
            "W2 runtime hardening only allows low-risk key: messages.groupChat.historyLimit"
        )

    run_id = run_id_now()
    evidence_dir_rel = args.evidence_dir or f"docs/design/modules/evidence/bpm-runtime/{run_id}"
    evidence_dir = root / evidence_dir_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)

    request_path = evidence_dir / "request.json"
    normalized_path = evidence_dir / "normalized_request.json"
    gate_input_path = evidence_dir / "gate_input.json"
    gate_output_path = evidence_dir / "gate_result.json"
    gate_report_path = evidence_dir / "gate_report.json"
    auth_path = evidence_dir / "authorization.json"
    apply_input_path = evidence_dir / "updater_apply_input.json"
    apply_output_path = evidence_dir / "updater_apply_output.json"
    apply_receipt_path = evidence_dir / "change_receipt_apply.json"
    rollback_input_path = evidence_dir / "updater_rollback_input.json"
    rollback_output_path = evidence_dir / "updater_rollback_output.json"
    rollback_receipt_path = evidence_dir / "change_receipt_rollback.json"
    verify_path = evidence_dir / "verification_report.json"

    dump_json(request_path, payload)

    change_request = payload.get("change_request")
    if not isinstance(change_request, dict):
        raise GovernedConfigChangeError("change_request must be object")
    delta = change_request.get("delta", 1)
    if not isinstance(delta, int):
        raise GovernedConfigChangeError("change_request.delta must be integer")

    hash_before, cfg_before = read_config_state(root, profile)
    value_before = get_nested(cfg_before, target_path)
    if not isinstance(value_before, int):
        raise GovernedConfigChangeError(f"target value is not integer at {target_path}: {value_before!r}")
    target_after = value_before + delta

    patch_obj = {"messages": {"groupChat": {"historyLimit": target_after}}}
    rollback_obj = {"messages": {"groupChat": {"historyLimit": value_before}}}
    patch_raw = json.dumps(patch_obj, ensure_ascii=False)
    rollback_raw = json.dumps(rollback_obj, ensure_ascii=False)

    normalized_request = {
        "timestamp": now_iso(),
        "objective_ref": payload["objective_ref"],
        "requester": payload["requester"],
        "target_path": target_path,
        "value_before": value_before,
        "target_after": target_after,
        "delta": delta,
        "base_hash": hash_before,
        "patch_raw": patch_raw,
        "rollback_patch_raw": rollback_raw,
    }
    dump_json(normalized_path, normalized_request)

    gate_input = {
        "objective_ref": payload["objective_ref"],
        "change_request": {
            "target_scope": {"path": target_path},
            "delta": delta,
        },
        "rollback_plan": payload.get("rollback_plan"),
        "evidence_refs": payload.get("evidence_refs", []),
    }
    dump_json(gate_input_path, gate_input)

    gate_cmd = [
        "python3",
        "skills/system/config-change-gatekeeper/scripts/config_change_gatekeeper_runner.py",
        "--input",
        to_rel(gate_input_path, root),
        "--output",
        to_rel(gate_output_path, root),
        "--report",
        to_rel(gate_report_path, root),
    ]
    gate_rc, gate_output = invoke_runner(root, gate_cmd, gate_output_path)

    if gate_rc not in (0, 2):
        raise GovernedConfigChangeError(f"gatekeeper runner failed unexpectedly: rc={gate_rc}")

    gate_approval = gate_output.get("approval")
    if gate_approval != "allow":
        final_payload = {
            "final_output": "governed-config-change denied at gate",
            "evidence_refs": [
                to_rel(request_path, root),
                to_rel(normalized_path, root),
                to_rel(gate_input_path, root),
                to_rel(gate_output_path, root),
                to_rel(gate_report_path, root),
            ],
            "verdict": "deny",
            "change_receipt": {},
            "reason": gate_output.get("reason", "gate denied"),
        }
        return finalize(root, output_path, final_payload, 2)

    authorization = payload.get("authorization")
    auth_ok, auth_reason = validate_authorization(authorization, target_path)
    auth_payload = {
        "timestamp": now_iso(),
        "decision": "allow" if auth_ok else "deny",
        "reason": auth_reason,
        "authorization": authorization,
        "target_path": target_path,
    }
    dump_json(auth_path, auth_payload)
    if not auth_ok:
        final_payload = {
            "final_output": "governed-config-change denied at authorization",
            "evidence_refs": [
                to_rel(request_path, root),
                to_rel(normalized_path, root),
                to_rel(gate_output_path, root),
                to_rel(auth_path, root),
            ],
            "verdict": "deny",
            "change_receipt": {},
            "reason": auth_reason,
        }
        return finalize(root, output_path, final_payload, 2)

    apply_input = {
        "base_hash": hash_before,
        "patch_raw": patch_raw,
        "rollback_plan": payload.get("rollback_plan"),
        "authorization": authorization,
        "target_path": target_path,
    }
    dump_json(apply_input_path, apply_input)

    apply_cmd = [
        "python3",
        "skills/system/system-config-updater/scripts/system_config_updater_runner.py",
        "--input",
        to_rel(apply_input_path, root),
        "--output",
        to_rel(apply_output_path, root),
        "--receipt",
        to_rel(apply_receipt_path, root),
    ]
    if profile:
        apply_cmd.extend(["--openclaw-profile", profile])

    apply_rc, apply_output = invoke_runner(root, apply_cmd, apply_output_path)
    if apply_rc != 0 or apply_output.get("execution_status") != "success":
        final_payload = {
            "final_output": "governed-config-change failed at apply stage",
            "evidence_refs": [
                to_rel(request_path, root),
                to_rel(gate_output_path, root),
                to_rel(auth_path, root),
                to_rel(apply_input_path, root),
                to_rel(apply_output_path, root),
                to_rel(apply_receipt_path, root),
            ],
            "verdict": "fail",
            "change_receipt": {
                "apply_receipt_ref": to_rel(apply_receipt_path, root),
            },
            "reason": apply_output.get("reason", "apply failed"),
        }
        return finalize(root, output_path, final_payload, 2)

    hash_after_apply, cfg_after_apply = read_config_state(root, profile)
    value_after_apply = get_nested(cfg_after_apply, target_path)

    rollback_input = {
        "base_hash": hash_after_apply,
        "patch_raw": rollback_raw,
        "rollback_plan": payload.get("rollback_plan"),
        "authorization": authorization,
        "target_path": target_path,
    }
    dump_json(rollback_input_path, rollback_input)

    rollback_cmd = [
        "python3",
        "skills/system/system-config-updater/scripts/system_config_updater_runner.py",
        "--input",
        to_rel(rollback_input_path, root),
        "--output",
        to_rel(rollback_output_path, root),
        "--receipt",
        to_rel(rollback_receipt_path, root),
    ]
    if profile:
        rollback_cmd.extend(["--openclaw-profile", profile])

    rollback_rc, rollback_output = invoke_runner(root, rollback_cmd, rollback_output_path)
    hash_after_rollback, cfg_after_rollback = read_config_state(root, profile)
    value_after_rollback = get_nested(cfg_after_rollback, target_path)

    verify_payload = {
        "timestamp": now_iso(),
        "target_path": target_path,
        "value_before": value_before,
        "value_after_apply": value_after_apply,
        "value_after_rollback": value_after_rollback,
        "hash_before": hash_before,
        "hash_after_apply": hash_after_apply,
        "hash_after_rollback": hash_after_rollback,
        "apply_value_match": value_after_apply == target_after,
        "rollback_value_restored": value_after_rollback == value_before,
        "hash_changed_on_apply": hash_after_apply != hash_before,
        "hash_changed_on_rollback": hash_after_rollback != hash_after_apply,
        "rollback_runner_status": rollback_output.get("execution_status"),
        "rollback_runner_rc": rollback_rc,
    }
    dump_json(verify_path, verify_payload)

    rollback_ok = rollback_rc == 0 and rollback_output.get("execution_status") == "success"
    verify_ok = (
        verify_payload["apply_value_match"]
        and verify_payload["rollback_value_restored"]
        and verify_payload["hash_changed_on_apply"]
    )

    verdict = "pass" if (rollback_ok and verify_ok) else "fail"
    exit_code = 0 if verdict == "pass" else 2
    final_payload = {
        "final_output": "governed-config-change completed" if verdict == "pass" else "governed-config-change failed",
        "evidence_refs": [
            to_rel(request_path, root),
            to_rel(normalized_path, root),
            to_rel(gate_input_path, root),
            to_rel(gate_output_path, root),
            to_rel(gate_report_path, root),
            to_rel(auth_path, root),
            to_rel(apply_input_path, root),
            to_rel(apply_output_path, root),
            to_rel(apply_receipt_path, root),
            to_rel(rollback_input_path, root),
            to_rel(rollback_output_path, root),
            to_rel(rollback_receipt_path, root),
            to_rel(verify_path, root),
        ],
        "verdict": verdict,
        "change_receipt": {
            "apply_receipt_ref": to_rel(apply_receipt_path, root),
            "rollback_receipt_ref": to_rel(rollback_receipt_path, root),
            "hash_before": hash_before,
            "hash_after_apply": hash_after_apply,
            "hash_after_rollback": hash_after_rollback,
        },
        "run_id": run_id,
        "evidence_dir": evidence_dir_rel,
    }
    return finalize(root, output_path, final_payload, exit_code)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GovernedConfigChangeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
