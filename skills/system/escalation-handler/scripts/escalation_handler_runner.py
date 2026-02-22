#!/usr/bin/env python3
"""Executable runner for sys.bpm.escalation-handler."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class EscalationHandlerError(RuntimeError):
    """Unexpected escalation handler failure."""


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
        raise EscalationHandlerError("not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def resolve_path(root: Path, raw: str) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    return (root / p).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EscalationHandlerError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EscalationHandlerError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise EscalationHandlerError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def required_chain_ok(chain: List[str]) -> bool:
    required = ["actor", "owner", "bpm", "admin", "human"]
    return chain == required


def next_hops(chain: List[str], current_owner: str) -> List[str]:
    if current_owner not in chain:
        return []
    idx = chain.index(current_owner)
    if idx >= len(chain) - 1:
        return []
    return chain[idx + 1 :]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute governed escalation chain for runtime anomalies")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--record", required=True, help="Escalation record output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    ts = now_iso()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    record_path = resolve_path(root, args.record)

    request = load_json(input_path)

    try:
        incident_ref = request.get("incident_ref")
        escalation_policy_ref = request.get("escalation_policy_ref")
        current_owner = request.get("current_owner")
        evidence_ref = request.get("evidence_ref")

        if not isinstance(incident_ref, str) or not incident_ref.strip():
            raise EscalationHandlerError("missing_incident_ref")
        if not isinstance(escalation_policy_ref, str) or not escalation_policy_ref.strip():
            raise EscalationHandlerError("missing_escalation_policy_ref")
        if not isinstance(current_owner, str) or not current_owner.strip():
            raise EscalationHandlerError("missing_current_owner")
        if not isinstance(evidence_ref, str) or not evidence_ref.strip():
            raise EscalationHandlerError("missing_evidence_ref")

        evidence_path = resolve_path(root, evidence_ref.strip())
        if not evidence_path.exists():
            raise EscalationHandlerError("incident_evidence_unreachable")

        policy = load_json(resolve_path(root, escalation_policy_ref.strip()))
        incident = load_json(resolve_path(root, incident_ref.strip()))

        chain = policy.get("escalation_chain")
        if not isinstance(chain, list) or not all(isinstance(item, str) for item in chain):
            raise EscalationHandlerError("escalation_chain_invalid")
        normalized_chain = [item.strip() for item in chain]
        if not required_chain_ok(normalized_chain):
            raise EscalationHandlerError("escalation_chain_missing_required_hop")

        owner = current_owner.strip()
        if owner not in normalized_chain:
            raise EscalationHandlerError("current_owner_not_in_chain")

        severity = str(incident.get("severity") or "").lower()
        reason = str(incident.get("reason") or "").strip()
        if not severity or not reason:
            raise EscalationHandlerError("incident_missing_severity_or_reason")

        requested_target = incident.get("requested_target")
        hops = next_hops(normalized_chain, owner)
        if isinstance(requested_target, str) and requested_target.strip():
            req = requested_target.strip()
            if not hops or req != hops[0]:
                raise EscalationHandlerError("escalation_target_bypasses_governance_chain")

        trace: List[Dict[str, Any]] = []
        decision = "resolve"
        final_owner = owner

        if severity in {"critical", "high"}:
            decision = "escalate"
            for hop in hops:
                trace.append({"from": final_owner, "to": hop, "ts": ts})
                final_owner = hop
                if hop == "admin":
                    break
            if final_owner == owner:
                raise EscalationHandlerError("escalation_chain_no_progress")
        elif severity == "medium":
            if hops:
                decision = "escalate"
                final_owner = hops[0]
                trace.append({"from": owner, "to": final_owner, "ts": ts})
        else:
            decision = "resolve"

        if decision == "escalate" and not trace:
            raise EscalationHandlerError("escalation_trace_empty")
        if final_owner not in normalized_chain:
            raise EscalationHandlerError("final_owner_out_of_chain")

        record = {
            "timestamp": ts,
            "incident_ref": incident_ref,
            "decision": decision,
            "final_owner": final_owner,
            "trace": trace,
            "reason": reason,
            "severity": severity,
        }
        dump_json(record_path, record)

        output = {
            "escalation_ref": to_rel(record_path, root),
            "final_owner": final_owner,
            "escalation_decision": decision,
            "escalation_trace": trace,
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 0

    except EscalationHandlerError as exc:
        failure = {
            "timestamp": ts,
            "status": "failed",
            "reason": str(exc),
            "fail_closed": True,
        }
        dump_json(record_path, failure)
        output = {
            "failure_code": "escalation_handler_failed",
            "reason": str(exc),
            "escalation_ref": to_rel(record_path, root),
            "final_owner": "",
            "escalation_decision": "fail",
            "escalation_trace": [],
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EscalationHandlerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
