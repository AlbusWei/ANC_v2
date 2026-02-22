#!/usr/bin/env python3
"""Executable runner for system.control.config-change-gatekeeper."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


class GatekeeperError(RuntimeError):
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
        raise GatekeeperError("not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GatekeeperError(f"input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GatekeeperError(f"input JSON invalid: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise GatekeeperError("input payload must be an object")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def normalize_evidence_refs(value: Any) -> Tuple[List[str], List[str]]:
    refs: List[str] = []
    errors: List[str] = []

    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                refs.append(item.strip())
            else:
                errors.append("evidence_refs contains non-string or empty item")
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not key.strip():
                errors.append("evidence_refs key must be non-empty string")
                continue
            if isinstance(item, str) and item.strip():
                refs.append(item.strip())
            else:
                errors.append(f"evidence_refs.{key} must be non-empty string")
    else:
        errors.append("evidence_refs must be a list or object")

    if not refs:
        errors.append("evidence_refs must be non-empty")
    return refs, errors


def extract_target_path(change_request: Dict[str, Any]) -> str | None:
    target_scope = change_request.get("target_scope")
    if isinstance(target_scope, dict):
        path = target_scope.get("path")
        if isinstance(path, str) and path.strip():
            return path.strip()
    if isinstance(target_scope, str) and target_scope.strip():
        return target_scope.strip()
    return None


def classify_risk(target_path: str, delta: int | None) -> str:
    if target_path == "messages.groupChat.historyLimit":
        if delta is None:
            return "low"
        if abs(delta) <= 20:
            return "low"
        return "medium"
    if target_path.startswith("messages."):
        return "medium"
    return "high"


def build_decision(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    required_fields = ["objective_ref", "change_request", "rollback_plan", "evidence_refs"]
    errors: List[str] = []
    checks: List[Dict[str, Any]] = []

    for field in required_fields:
        ok = field in payload
        checks.append({"name": f"required:{field}", "ok": ok})
        if not ok:
            errors.append(f"missing required field: {field}")

    change_request = payload.get("change_request")
    if not isinstance(change_request, dict):
        errors.append("change_request must be an object")
        change_request = {}

    rollback_plan = payload.get("rollback_plan")
    if not isinstance(rollback_plan, dict) or not rollback_plan:
        errors.append("rollback_plan must be a non-empty object")
    elif rollback_plan.get("executable") is False:
        errors.append("rollback_plan.executable is false")

    evidence_refs, evidence_errors = normalize_evidence_refs(payload.get("evidence_refs"))
    errors.extend(evidence_errors)
    checks.append({"name": "evidence_refs_non_empty", "ok": len(evidence_refs) > 0})

    target_path = extract_target_path(change_request)
    if not target_path:
        errors.append("change_request.target_scope.path is required")
    checks.append({"name": "target_scope_path", "ok": bool(target_path)})

    raw_delta = change_request.get("delta")
    delta: int | None = None
    if raw_delta is not None:
        if isinstance(raw_delta, int):
            delta = raw_delta
        else:
            errors.append("change_request.delta must be integer when provided")

    risk_level = classify_risk(target_path or "unknown", delta)
    approval = "allow" if not errors else "deny"
    reason = "gate passed" if approval == "allow" else "; ".join(errors)

    report = {
        "timestamp": now_iso(),
        "approval": approval,
        "risk_level": risk_level,
        "reason": reason,
        "objective_ref": payload.get("objective_ref"),
        "target_path": target_path,
        "delta": delta,
        "checks": checks,
        "errors": errors,
        "evidence_refs": evidence_refs,
    }
    return report, (0 if approval == "allow" else 2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run config-change gatekeeper checks")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--report",
        default=None,
        help="Optional gate report path; default is next to output as gate_report.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = root / input_path
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path
    report_path = Path(args.report) if args.report else output_path.with_name("gate_report.json")
    if not report_path.is_absolute():
        report_path = root / report_path

    payload = load_json(input_path)
    report, exit_code = build_decision(payload)

    report_rel = to_rel(report_path, root)
    output = {
        "approval": report["approval"],
        "risk_level": report["risk_level"],
        "reason": report["reason"],
        "gate_report_ref": report_rel,
        "timestamp": report["timestamp"],
    }

    dump_json(report_path, report)
    dump_json(output_path, output)
    print(to_rel(output_path, root))
    return exit_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GatekeeperError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
