#!/usr/bin/env python3
"""Executable runner for escalation process."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class EscalationProcessError(RuntimeError):
    """Fail-closed runtime error for escalation process."""


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
        raise EscalationProcessError("not inside a git repository")
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
        raise EscalationProcessError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EscalationProcessError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise EscalationProcessError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run escalation process")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--trace", default="", help="Escalation trace output path")
    return parser.parse_args()


def _fail_closed(
    *,
    root: Path,
    output_path: Path,
    trace_path: Path,
    reason: str,
) -> int:
    trace = {
        "status": "failed",
        "reason": reason,
        "generated_at": now_iso(),
    }
    dump_json(trace_path, trace)
    output = {
        "escalation_ref": to_rel(trace_path, root),
        "escalation_trace": [],
        "final_owner": "",
        "escalation_decision": "failed",
        "reasons": [reason],
    }
    dump_json(output_path, output)
    print(to_rel(output_path, root))
    return 2


def _next_owner(chain: List[str], current: str) -> str:
    idx = chain.index(current)
    if idx >= len(chain) - 1:
        return current
    return chain[idx + 1]


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    trace_path = (
        resolve_path(root, args.trace)
        if args.trace.strip()
        else output_path.parent / "escalation_trace_record.json"
    )

    request = load_json(input_path)
    required = ["incident_ref", "severity", "current_owner", "escalation_policy_ref", "evidence_ref"]
    for field in required:
        value = request.get(field)
        if not isinstance(value, str) or not value.strip():
            return _fail_closed(
                root=root,
                output_path=output_path,
                trace_path=trace_path,
                reason=f"missing_{field}",
            )

    severity = str(request["severity"]).strip().lower()
    if severity not in {"low", "medium", "high", "critical"}:
        return _fail_closed(
            root=root,
            output_path=output_path,
            trace_path=trace_path,
            reason="invalid_severity",
        )

    evidence_path = resolve_path(root, str(request["evidence_ref"]))
    if not evidence_path.exists():
        return _fail_closed(
            root=root,
            output_path=output_path,
            trace_path=trace_path,
            reason="evidence_unreachable",
        )

    try:
        _ = load_json(resolve_path(root, str(request["incident_ref"])))
        policy = load_json(resolve_path(root, str(request["escalation_policy_ref"])))
    except EscalationProcessError:
        return _fail_closed(
            root=root,
            output_path=output_path,
            trace_path=trace_path,
            reason="incident_or_policy_unreachable",
        )

    chain = policy.get("escalation_chain")
    required_chain = ["actor", "owner", "bpm", "admin", "human"]
    if not isinstance(chain, list) or [str(x).strip() for x in chain] != required_chain:
        return _fail_closed(
            root=root,
            output_path=output_path,
            trace_path=trace_path,
            reason="invalid_escalation_chain",
        )

    current_owner = str(request["current_owner"]).strip()
    if current_owner not in required_chain:
        return _fail_closed(
            root=root,
            output_path=output_path,
            trace_path=trace_path,
            reason="current_owner_not_in_chain",
        )

    decision = "resolved"
    final_owner = current_owner
    trace: List[Dict[str, Any]] = []

    if severity == "low":
        decision = "resolved"
    elif severity == "medium":
        decision = "escalated"
        target = _next_owner(required_chain, current_owner)
        if target == current_owner:
            return _fail_closed(
                root=root,
                output_path=output_path,
                trace_path=trace_path,
                reason="escalation_no_progress",
            )
        trace.append({"from": current_owner, "to": target, "ts": now_iso()})
        final_owner = target
    elif severity == "high":
        decision = "escalated"
        cursor = current_owner
        while cursor != "admin":
            nxt = _next_owner(required_chain, cursor)
            if nxt == cursor:
                return _fail_closed(
                    root=root,
                    output_path=output_path,
                    trace_path=trace_path,
                    reason="admin_unreachable",
                )
            trace.append({"from": cursor, "to": nxt, "ts": now_iso()})
            cursor = nxt
        final_owner = cursor
    else:
        decision = "human_required"
        cursor = current_owner
        while cursor != "human":
            nxt = _next_owner(required_chain, cursor)
            if nxt == cursor:
                return _fail_closed(
                    root=root,
                    output_path=output_path,
                    trace_path=trace_path,
                    reason="human_unreachable",
                )
            trace.append({"from": cursor, "to": nxt, "ts": now_iso()})
            cursor = nxt
        final_owner = cursor

    record = {
        "timestamp": now_iso(),
        "incident_ref": request["incident_ref"],
        "severity": severity,
        "current_owner": current_owner,
        "final_owner": final_owner,
        "escalation_decision": decision,
        "escalation_trace": trace,
    }
    dump_json(trace_path, record)

    output = {
        "escalation_ref": to_rel(trace_path, root),
        "escalation_trace": trace,
        "final_owner": final_owner,
        "escalation_decision": decision,
        "reasons": ["governed_chain_routing_completed"],
    }
    dump_json(output_path, output)
    print(to_rel(output_path, root))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EscalationProcessError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
