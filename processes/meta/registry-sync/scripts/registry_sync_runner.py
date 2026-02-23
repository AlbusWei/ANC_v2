#!/usr/bin/env python3
"""Executable runner for registry-sync process."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class RegistrySyncError(RuntimeError):
    """Fail-closed runtime error for registry-sync."""


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
        raise RegistrySyncError("not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistrySyncError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RegistrySyncError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RegistrySyncError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run registry-sync process")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--sync-record", default="", help="Sync record output path")
    parser.add_argument("--verify-report", default="", help="Verify report output path")
    return parser.parse_args()


def _fail_closed(
    *,
    root: Path,
    output_path: Path,
    sync_record_path: Path,
    verify_report_path: Path,
    decision: str,
    reason: str,
) -> int:
    dump_json(
        verify_report_path,
        {
            "status": "failed",
            "decision": decision,
            "reason": reason,
            "generated_at": now_iso(),
        },
    )
    dump_json(
        sync_record_path,
        {
            "status": "failed",
            "decision": decision,
            "reason": reason,
            "generated_at": now_iso(),
        },
    )
    dump_json(
        output_path,
        {
            "registry_sync_ref": to_rel(sync_record_path, root),
            "registry_verify_report_ref": to_rel(verify_report_path, root),
            "sync_decision": decision,
            "reasons": [reason],
        },
    )
    print(to_rel(output_path, root))
    return 2


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    sync_record_path = (
        resolve_path(root, args.sync_record)
        if args.sync_record.strip()
        else output_path.parent / "registry_sync_record.json"
    )
    verify_report_path = (
        resolve_path(root, args.verify_report)
        if args.verify_report.strip()
        else output_path.parent / "registry_verify_report.json"
    )

    request = load_json(input_path)

    required = [
        "target_registry_ref",
        "registry_patch_plan_ref",
        "requested_transition_ref",
        "verify_scope",
        "evidence_ref",
    ]
    for field in required:
        value = request.get(field)
        if not isinstance(value, str) or not value.strip():
            return _fail_closed(
                root=root,
                output_path=output_path,
                sync_record_path=sync_record_path,
                verify_report_path=verify_report_path,
                decision="fail",
                reason=f"missing_{field}",
            )

    target_registry_ref = str(request["target_registry_ref"]).strip()
    allowed = {
        "shared/registry/skill_registry.json",
        "shared/registry/process_registry.json",
        "shared/registry/agent_directory.json",
    }
    if target_registry_ref not in allowed:
        return _fail_closed(
            root=root,
            output_path=output_path,
            sync_record_path=sync_record_path,
            verify_report_path=verify_report_path,
            decision="fail",
            reason="target_registry_not_allowed",
        )

    try:
        _ = load_json(resolve_path(root, str(request["registry_patch_plan_ref"])))
    except RegistrySyncError:
        return _fail_closed(
            root=root,
            output_path=output_path,
            sync_record_path=sync_record_path,
            verify_report_path=verify_report_path,
            decision="fail",
            reason="patch_plan_unreachable",
        )

    evidence_path = resolve_path(root, str(request["evidence_ref"]))
    if not evidence_path.exists():
        return _fail_closed(
            root=root,
            output_path=output_path,
            sync_record_path=sync_record_path,
            verify_report_path=verify_report_path,
            decision="blocked",
            reason="evidence_unreachable",
        )

    verify_proc = subprocess.run(
        ["python3", "shared/registry/registry_contract_tool.py", "verify"],
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
    )

    verify_report = {
        "timestamp": now_iso(),
        "command": "python3 shared/registry/registry_contract_tool.py verify",
        "return_code": verify_proc.returncode,
        "stdout_tail": "\n".join(verify_proc.stdout.splitlines()[-30:]),
        "stderr_tail": "\n".join(verify_proc.stderr.splitlines()[-30:]),
    }
    dump_json(verify_report_path, verify_report)

    if verify_proc.returncode != 0:
        return _fail_closed(
            root=root,
            output_path=output_path,
            sync_record_path=sync_record_path,
            verify_report_path=verify_report_path,
            decision="fail",
            reason="registry_verify_failed",
        )

    sync_record = {
        "timestamp": now_iso(),
        "target_registry_ref": target_registry_ref,
        "requested_transition_ref": request["requested_transition_ref"],
        "verify_scope": request["verify_scope"],
        "sync_decision": "pass",
        "reasons": ["registry_contract_verify_passed"],
    }
    dump_json(sync_record_path, sync_record)

    output = {
        "registry_sync_ref": to_rel(sync_record_path, root),
        "registry_verify_report_ref": to_rel(verify_report_path, root),
        "sync_decision": "pass",
        "reasons": ["registry_contract_verify_passed"],
    }
    dump_json(output_path, output)
    print(to_rel(output_path, root))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RegistrySyncError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
