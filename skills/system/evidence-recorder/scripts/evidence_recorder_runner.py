#!/usr/bin/env python3
"""Executable runner for sys.bpm.evidence-recorder."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class EvidenceRecorderError(RuntimeError):
    """Unexpected evidence recorder failure."""


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
        raise EvidenceRecorderError("not inside a git repository")
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
        raise EvidenceRecorderError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvidenceRecorderError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise EvidenceRecorderError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record trigger runtime evidence and traceability links")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--receipt", required=True, help="Trigger receipt output path")
    parser.add_argument("--index", required=True, help="Evidence index JSONL path")
    parser.add_argument("--trace", required=True, help="Traceability link output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    ts = now_iso()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    receipt_path = resolve_path(root, args.receipt)
    index_path = resolve_path(root, args.index)
    trace_path = resolve_path(root, args.trace)

    request = load_json(input_path)

    try:
        trigger_id = request.get("trigger_id")
        if not isinstance(trigger_id, str) or not trigger_id.strip():
            raise EvidenceRecorderError("missing_trigger_id")
        instance_id = request.get("instance_id")
        if not isinstance(instance_id, str) or not instance_id.strip():
            raise EvidenceRecorderError("missing_instance_id")
        decision = request.get("decision")
        if not isinstance(decision, str) or not decision.strip():
            raise EvidenceRecorderError("missing_decision")

        evidence_payload_ref = request.get("evidence_payload_ref")
        if not isinstance(evidence_payload_ref, str) or not evidence_payload_ref.strip():
            raise EvidenceRecorderError("missing_evidence_payload_ref")
        evidence_payload = load_json(resolve_path(root, evidence_payload_ref.strip()))

        actor = evidence_payload.get("actor")
        evidence_ts = evidence_payload.get("timestamp")
        if not isinstance(actor, str) or not actor.strip():
            raise EvidenceRecorderError("evidence_payload_missing_actor")
        if not isinstance(evidence_ts, str) or not evidence_ts.strip():
            raise EvidenceRecorderError("evidence_payload_missing_timestamp")

        session_id = str(evidence_payload.get("session_id") or "")
        parent_session_id = evidence_payload.get("parent_session_id")

        receipt_payload = {
            "timestamp": ts,
            "trigger_id": trigger_id,
            "instance_id": instance_id,
            "decision": decision,
            "actor": actor,
            "evidence_payload_ref": evidence_payload_ref,
            "session_id": session_id,
        }
        dump_json(receipt_path, receipt_payload)

        index_entry = {
            "timestamp": ts,
            "trigger_id": trigger_id,
            "instance_id": instance_id,
            "decision": decision,
            "receipt_ref": to_rel(receipt_path, root),
            "session_id": session_id,
        }
        append_jsonl(index_path, index_entry)

        trace_payload = {
            "timestamp": ts,
            "trigger_to_instance": {
                "trigger_id": trigger_id,
                "instance_id": instance_id,
            },
            "instance_to_trigger": {
                "instance_id": instance_id,
                "trigger_id": trigger_id,
            },
            "session_binding": {
                "session_id": session_id,
                "parent_session_id": parent_session_id,
            },
        }
        dump_json(trace_path, trace_payload)

        output = {
            "trigger_receipt_ref": to_rel(receipt_path, root),
            "evidence_index_ref": to_rel(index_path, root),
            "traceability_link_ref": to_rel(trace_path, root),
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 0

    except EvidenceRecorderError as exc:
        failure_payload = {
            "timestamp": ts,
            "status": "failed",
            "reason": str(exc),
            "fail_closed": True,
        }
        dump_json(receipt_path, failure_payload)
        dump_json(trace_path, failure_payload)
        output = {
            "failure_code": "evidence_record_failed",
            "reason": str(exc),
            "trigger_receipt_ref": to_rel(receipt_path, root),
            "evidence_index_ref": to_rel(index_path, root),
            "traceability_link_ref": to_rel(trace_path, root),
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EvidenceRecorderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
