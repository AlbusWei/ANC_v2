#!/usr/bin/env python3
"""Executable runner for sys.bpm.trigger-ingress-normalizer."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple


class NormalizerError(RuntimeError):
    """Unexpected normalizer failure."""


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
        raise NormalizerError("not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise NormalizerError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise NormalizerError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise NormalizerError(f"json root must be object: {path}")
    return payload


def parse_rfc3339(raw: Any, field: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise NormalizerError(f"{field} must be non-empty RFC3339 string")
    text = raw.strip()
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        stamp = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise NormalizerError(f"{field} invalid RFC3339: {text}") from exc
    if stamp.tzinfo is None:
        raise NormalizerError(f"{field} must include timezone")
    return stamp.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def normalize_payload_refs(root: Path, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    payload_ref = payload.get("payload_ref")
    if not isinstance(payload_ref, str) or not payload_ref.strip():
        raise NormalizerError("payload_ref must be non-empty string")
    payload_path = resolve_path(root, payload_ref.strip())
    payload_obj = load_json(payload_path)
    return payload_obj, payload_ref.strip()


def compute_bucket(received_at: str) -> str:
    stamp = datetime.fromisoformat(received_at.replace("Z", "+00:00"))
    minute_bucket = stamp.replace(second=0)
    return minute_bucket.strftime("%Y%m%dT%H%M")


def stable_trigger_id(trigger_source: str, payload: Dict[str, Any], canonical: Dict[str, Any]) -> str:
    event_id = payload.get("event_id")
    if isinstance(event_id, str) and event_id.strip():
        seed = f"{trigger_source}|{event_id.strip()}"
    else:
        fallback_fields = [
            trigger_source,
            str(canonical.get("canonical_event") or ""),
            str(canonical.get("entity_type") or ""),
            str(canonical.get("entity_id") or ""),
            str(canonical.get("from_status") or ""),
            str(canonical.get("to_status") or ""),
            str(canonical.get("emitted_by") or ""),
            str(canonical.get("time_bucket") or ""),
        ]
        if any(not field for field in fallback_fields):
            raise NormalizerError("cannot_build_trigger_id_from_primary_or_fallback")
        seed = "|".join(fallback_fields)

    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return f"trg-{digest[:20]}"


def validate_trigger_type(raw: Any) -> str:
    if not isinstance(raw, str):
        raise NormalizerError("trigger_type must be string")
    trigger_type = raw.strip().lower()
    if trigger_type not in {"schedule", "heartbeat", "event", "threshold"}:
        raise NormalizerError(f"unsupported_trigger_type:{trigger_type}")
    return trigger_type


def ensure_event_minimum_fields(payload: Dict[str, Any]) -> None:
    required = ["event_time", "entity_type", "entity_id", "from_status", "to_status", "emitted_by"]
    missing = [field for field in required if not isinstance(payload.get(field), str) or not str(payload.get(field)).strip()]
    if missing:
        raise NormalizerError(f"missing_event_minimum_fields:{','.join(missing)}")
    if not isinstance(payload.get("transition_evidence_ref"), str) and not isinstance(payload.get("evidence_ref"), str):
        raise NormalizerError("missing_transition_evidence_ref")


def build_outputs(
    root: Path,
    args: argparse.Namespace,
    canonical_payload: Dict[str, Any],
    report_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
) -> None:
    canonical_path = Path(args.canonical)
    if not canonical_path.is_absolute():
        canonical_path = root / canonical_path

    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = root / report_path

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path

    dump_json(canonical_path, canonical_payload)
    dump_json(report_path, report_payload)

    final = dict(output_payload)
    final["canonical_trigger_ref"] = to_rel(canonical_path, root)
    final["normalization_report_ref"] = to_rel(report_path, root)

    dump_json(output_path, final)
    print(to_rel(output_path, root))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize trigger ingress payload into canonical envelope")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--canonical", required=True, help="Canonical trigger JSON path")
    parser.add_argument("--report", required=True, help="Normalization report JSON path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = root / input_path

    request = load_json(input_path)
    ts = now_iso()

    try:
        trigger_type = validate_trigger_type(request.get("trigger_type"))
        trigger_source_raw = request.get("trigger_source")
        if not isinstance(trigger_source_raw, str) or not trigger_source_raw.strip():
            raise NormalizerError("trigger_source must be non-empty string")
        trigger_source = trigger_source_raw.strip()

        received_at = parse_rfc3339(request.get("received_at"), "received_at")
        payload_obj, payload_ref = normalize_payload_refs(root, request)

        if trigger_type == "event":
            ensure_event_minimum_fields(payload_obj)

        canonical = {
            "trigger_type": trigger_type,
            "trigger_source": trigger_source,
            "received_at": received_at,
            "time_bucket": compute_bucket(received_at),
            "event_id": payload_obj.get("event_id"),
            "event_time": payload_obj.get("event_time"),
            "entity_type": payload_obj.get("entity_type"),
            "entity_id": payload_obj.get("entity_id"),
            "from_status": payload_obj.get("from_status"),
            "to_status": payload_obj.get("to_status"),
            "emitted_by": payload_obj.get("emitted_by"),
            "canonical_event": payload_obj.get("canonical_event") or request.get("canonical_event"),
            "evidence_ref": payload_obj.get("transition_evidence_ref") or payload_obj.get("evidence_ref"),
            "payload_ref": payload_ref,
            "normalized_at": ts,
        }
        trigger_id = stable_trigger_id(trigger_source, payload_obj, canonical)
        canonical["trigger_id"] = trigger_id

        report = {
            "timestamp": ts,
            "status": "ok",
            "trigger_type": trigger_type,
            "trigger_source": trigger_source,
            "checks": {
                "received_at_rfc3339": True,
                "payload_ref_reachable": True,
                "event_contract_valid": True if trigger_type != "event" else True,
            },
        }

        output = {
            "status": "ok",
            "trigger_id": trigger_id,
        }

        build_outputs(root, args, canonical, report, output)
        return 0

    except NormalizerError as exc:
        report = {
            "timestamp": ts,
            "status": "failed",
            "reason": str(exc),
            "checks": {
                "fail_closed": True,
            },
        }
        output = {
            "status": "failed",
            "failure_code": "normalization_failed",
            "reason": str(exc),
            "trigger_id": "",
        }
        build_outputs(
            root,
            args,
            canonical_payload={
                "status": "failed",
                "reason": str(exc),
                "normalized_at": ts,
            },
            report_payload=report,
            output_payload=output,
        )
        return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NormalizerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
