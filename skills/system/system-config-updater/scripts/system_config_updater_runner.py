#!/usr/bin/env python3
"""Executable runner for system.admin.system-config-updater."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


class ConfigUpdaterError(RuntimeError):
    """Unexpected runner failure."""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise ConfigUpdaterError("not inside a git repository")
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
    raise ConfigUpdaterError("no JSON payload found in command output")


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigUpdaterError(f"input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigUpdaterError(f"input JSON invalid: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ConfigUpdaterError("input payload must be object")
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


def summarize_patch(patch_obj: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "top_level_keys": sorted(patch_obj.keys()),
        "messages.groupChat.historyLimit": get_nested(patch_obj, "messages.groupChat.historyLimit"),
    }


def sanitize_patch_response(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {"raw_type": type(payload).__name__}
    keep: Dict[str, Any] = {}
    for key in ["ok", "valid", "hash", "issues", "warnings", "legacyIssues", "restart", "sentinel"]:
        if key in payload:
            keep[key] = payload[key]
    if "message" in payload:
        keep["message"] = payload["message"]
    if "error" in payload:
        keep["error"] = payload["error"]
    return keep


def is_transient_gateway_failure(proc: subprocess.CompletedProcess[str]) -> bool:
    text = (proc.stdout + "\n" + proc.stderr).lower()
    transient_markers = [
        "gateway closed",
        "abnormal closure",
        "econnrefused",
        "connection refused",
        "gateway call failed",
    ]
    return any(marker in text for marker in transient_markers)


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
        raise ConfigUpdaterError(
            "config.get failed\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )
    if proc is None:
        raise ConfigUpdaterError("config.get failed before execution")
    payload = parse_json_from_mixed_output(proc.stdout)
    if not isinstance(payload, dict):
        raise ConfigUpdaterError("config.get output must be object")
    hash_value = payload.get("hash")
    config_obj = payload.get("parsed") or payload.get("config")
    if not isinstance(hash_value, str) or not hash_value.strip():
        raise ConfigUpdaterError("config.get output missing hash")
    if not isinstance(config_obj, dict):
        raise ConfigUpdaterError("config.get output missing parsed/config object")
    return hash_value, config_obj


def validate_authorization(payload: Dict[str, Any]) -> Tuple[bool, str]:
    authorization = payload.get("authorization")
    if not isinstance(authorization, dict):
        return False, "authorization must be object"
    if authorization.get("approved") is not True:
        return False, "authorization.approved must be true"

    role = authorization.get("approved_by_role")
    if not isinstance(role, str) or not role.strip():
        return False, "authorization.approved_by_role must be non-empty string"
    if role not in {"admin", "human"}:
        return False, f"authorization role not allowed for config write: {role}"
    return True, "authorized"


def fail_closed_output(
    output_path: Path,
    receipt_path: Path,
    root: Path,
    hash_before: str,
    reason: str,
    failure_code: str,
    patch_summary: Dict[str, Any],
    target_path: str | None,
) -> int:
    receipt = {
        "timestamp": now_iso(),
        "execution_status": "failed",
        "failure_code": failure_code,
        "reason": reason,
        "hash_before": hash_before,
        "hash_after": hash_before,
        "target_path": target_path,
        "patch_summary": patch_summary,
        "rollback_status": "not_started",
    }
    output = {
        "hash_before": hash_before,
        "hash_after": hash_before,
        "execution_status": "failed",
        "reason": reason,
        "failure_code": failure_code,
        "receipt_ref": to_rel(receipt_path, root),
    }
    dump_json(receipt_path, receipt)
    dump_json(output_path, output)
    print(to_rel(output_path, root))
    return 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute hash-safe OpenClaw config patch")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--receipt",
        default=None,
        help="Optional change receipt JSON path; default is next to output as change_receipt.json",
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
    receipt_path = Path(args.receipt) if args.receipt else output_path.with_name("change_receipt.json")
    if not receipt_path.is_absolute():
        receipt_path = root / receipt_path

    payload = load_json(input_path)
    base_hash = payload.get("base_hash")
    patch_raw = payload.get("patch_raw")
    rollback_plan = payload.get("rollback_plan")
    target_path = payload.get("target_path")

    if not isinstance(base_hash, str) or not base_hash.strip():
        raise ConfigUpdaterError("base_hash must be non-empty string")
    if not isinstance(patch_raw, str) or not patch_raw.strip():
        raise ConfigUpdaterError("patch_raw must be non-empty JSON string")
    if not isinstance(rollback_plan, dict) or not rollback_plan:
        raise ConfigUpdaterError("rollback_plan must be non-empty object")
    if target_path is not None and (not isinstance(target_path, str) or not target_path.strip()):
        raise ConfigUpdaterError("target_path must be non-empty string when provided")

    try:
        patch_obj = json.loads(patch_raw)
    except json.JSONDecodeError as exc:
        raise ConfigUpdaterError(f"patch_raw is invalid JSON: {exc}") from exc
    if not isinstance(patch_obj, dict):
        raise ConfigUpdaterError("patch_raw JSON root must be object")

    hash_before, config_before = read_config_state(root, profile)
    patch_summary = summarize_patch(patch_obj)
    if isinstance(target_path, str):
        patch_summary["target_before"] = get_nested(config_before, target_path)

    auth_ok, auth_reason = validate_authorization(payload)
    if not auth_ok:
        return fail_closed_output(
            output_path=output_path,
            receipt_path=receipt_path,
            root=root,
            hash_before=hash_before,
            reason=auth_reason,
            failure_code="authorization_denied",
            patch_summary=patch_summary,
            target_path=target_path if isinstance(target_path, str) else None,
        )

    if hash_before != base_hash:
        return fail_closed_output(
            output_path=output_path,
            receipt_path=receipt_path,
            root=root,
            hash_before=hash_before,
            reason="base_hash mismatch",
            failure_code="base_hash_mismatch",
            patch_summary=patch_summary,
            target_path=target_path if isinstance(target_path, str) else None,
        )

    params = {"raw": patch_raw, "baseHash": base_hash}
    patch_cmd = ["openclaw"]
    if profile:
        patch_cmd.extend(["--profile", profile])
    patch_cmd.extend(["gateway", "call", "config.patch", "--params", json.dumps(params, ensure_ascii=False), "--json"])

    patch_proc: subprocess.CompletedProcess[str] | None = None
    patch_payload: Any = None
    patch_error = ""
    max_attempts = 4
    for attempt in range(1, max_attempts + 1):
        patch_proc = run_cmd(patch_cmd, root)
        if patch_proc.returncode == 0:
            try:
                patch_payload = parse_json_from_mixed_output(patch_proc.stdout)
                patch_error = ""
                break
            except ConfigUpdaterError as exc:
                patch_error = str(exc)
        else:
            patch_error = (
                f"config.patch command failed rc={patch_proc.returncode}; "
                f"stderr={patch_proc.stderr.strip() or '<empty>'}"
            )

        if attempt < max_attempts and patch_proc is not None and is_transient_gateway_failure(patch_proc):
            time.sleep(float(attempt))
            continue
        break

    if patch_error:
        return fail_closed_output(
            output_path=output_path,
            receipt_path=receipt_path,
            root=root,
            hash_before=hash_before,
            reason=patch_error,
            failure_code="patch_apply_failed",
            patch_summary=patch_summary,
            target_path=target_path if isinstance(target_path, str) else None,
        )

    if isinstance(patch_payload, dict) and patch_payload.get("ok") is False:
        reason = patch_payload.get("message") or patch_payload.get("error") or "config.patch rejected"
        return fail_closed_output(
            output_path=output_path,
            receipt_path=receipt_path,
            root=root,
            hash_before=hash_before,
            reason=str(reason),
            failure_code="patch_rejected",
            patch_summary=patch_summary,
            target_path=target_path if isinstance(target_path, str) else None,
        )

    hash_after, config_after = read_config_state(root, profile)
    if isinstance(target_path, str):
        patch_summary["target_after"] = get_nested(config_after, target_path)

    receipt = {
        "timestamp": now_iso(),
        "execution_status": "success",
        "hash_before": hash_before,
        "hash_after": hash_after,
        "target_path": target_path if isinstance(target_path, str) else None,
        "patch_summary": patch_summary,
        "rollback_status": "not_started",
        "patch_response": sanitize_patch_response(patch_payload),
    }
    output = {
        "hash_before": hash_before,
        "hash_after": hash_after,
        "execution_status": "success",
        "receipt_ref": to_rel(receipt_path, root),
        "patch_summary": patch_summary,
    }

    dump_json(receipt_path, receipt)
    dump_json(output_path, output)
    print(to_rel(output_path, root))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConfigUpdaterError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
