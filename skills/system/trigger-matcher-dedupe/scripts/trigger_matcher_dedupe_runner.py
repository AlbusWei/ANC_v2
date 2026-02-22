#!/usr/bin/env python3
"""Executable runner for sys.bpm.trigger-matcher-dedupe."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class MatcherError(RuntimeError):
    """Unexpected matcher failure."""


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
        raise MatcherError("not inside a git repository")
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
        raise MatcherError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MatcherError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise MatcherError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_policy(root: Path, raw_ref: Any, field: str) -> Dict[str, Any]:
    if not isinstance(raw_ref, str) or not raw_ref.strip():
        raise MatcherError(f"{field} must be non-empty string")
    return load_json(resolve_path(root, raw_ref.strip()))


def get_key(canonical: Dict[str, Any], key: str) -> str:
    value = canonical.get(key)
    return str(value).strip() if isinstance(value, str) else ""


def build_primary_key(canonical: Dict[str, Any]) -> str:
    source = get_key(canonical, "trigger_source")
    event_id = get_key(canonical, "event_id")
    if source and event_id:
        return f"{source}|{event_id}"
    return ""


def build_fallback_key(canonical: Dict[str, Any]) -> str:
    fields = [
        get_key(canonical, "trigger_source"),
        get_key(canonical, "canonical_event"),
        get_key(canonical, "entity_type"),
        get_key(canonical, "entity_id"),
        get_key(canonical, "from_status"),
        get_key(canonical, "to_status"),
        get_key(canonical, "emitted_by"),
        get_key(canonical, "time_bucket"),
    ]
    if any(not field for field in fields):
        return ""
    return "|".join(fields)


def load_ledger(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"entries": {}}
    payload = load_json(path)
    entries = payload.get("entries")
    if not isinstance(entries, dict):
        raise MatcherError(f"ledger.entries must be object: {path}")
    return payload


def validate_canonical_minimum(canonical: Dict[str, Any]) -> List[str]:
    required = ["trigger_id", "trigger_type", "trigger_source", "received_at"]
    errors: List[str] = []
    for field in required:
        if not get_key(canonical, field):
            errors.append(f"missing_canonical_field:{field}")
    return errors


def match_hit(canonical: Dict[str, Any], policy: Dict[str, Any]) -> bool:
    target = policy.get("target_process_id")
    if not isinstance(target, str) or not target.strip():
        raise MatcherError("target_process_id undefined in match_policy")

    allowed_types = policy.get("trigger_types", [])
    if allowed_types:
        if not isinstance(allowed_types, list) or not all(isinstance(item, str) for item in allowed_types):
            raise MatcherError("match_policy.trigger_types must be string array")
        if get_key(canonical, "trigger_type") not in {item.strip().lower() for item in allowed_types}:
            return False

    conditions = policy.get("conditions", {})
    if conditions:
        if not isinstance(conditions, dict):
            raise MatcherError("match_policy.conditions must be object")
        for key, expected in conditions.items():
            actual = canonical.get(key)
            if actual != expected:
                return False

    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Match canonical trigger and execute dedupe policy")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--dedupe-key", required=True, help="Dedupe key evidence output path")
    parser.add_argument("--evidence", required=True, help="Matcher evidence output path")
    parser.add_argument("--ledger", required=True, help="Dedupe ledger JSON path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    ts = now_iso()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    key_path = resolve_path(root, args.dedupe_key)
    evidence_path = resolve_path(root, args.evidence)
    ledger_path = resolve_path(root, args.ledger)

    request = load_json(input_path)

    try:
        canonical_ref = request.get("canonical_trigger_ref")
        if not isinstance(canonical_ref, str) or not canonical_ref.strip():
            raise MatcherError("canonical_trigger_ref must be non-empty string")
        canonical = load_json(resolve_path(root, canonical_ref.strip()))

        match_policy = load_policy(root, request.get("match_policy_ref"), "match_policy_ref")
        dedupe_policy = load_policy(root, request.get("dedupe_policy_ref"), "dedupe_policy_ref")

        errors = validate_canonical_minimum(canonical)
        if errors:
            raise MatcherError(";".join(errors))

        policy_primary = dedupe_policy.get("primary_key")
        if policy_primary != "source+event_id":
            raise MatcherError("dedupe_policy.primary_key must be source+event_id")
        fallback_fields = dedupe_policy.get("fallback_fields")
        if not isinstance(fallback_fields, list) or len(fallback_fields) < 8:
            raise MatcherError("dedupe_policy.fallback_fields invalid")

        hit = match_hit(canonical, match_policy)

        primary_key = build_primary_key(canonical)
        fallback_key = build_fallback_key(canonical)
        if not primary_key and not fallback_key:
            raise MatcherError("primary_and_fallback_keys_unavailable")

        ledger = load_ledger(ledger_path)
        entries = ledger.setdefault("entries", {})
        if not isinstance(entries, dict):
            raise MatcherError("ledger.entries must be object")

        p_tag = f"primary:{primary_key}" if primary_key else ""
        f_tag = f"fallback:{fallback_key}" if fallback_key else ""
        existing_primary = bool(p_tag and p_tag in entries)
        existing_fallback = bool(f_tag and f_tag in entries)

        selected_mode = "primary" if p_tag else "fallback"
        selected_tag = p_tag if selected_mode == "primary" else f_tag
        existing_selected = existing_primary if selected_mode == "primary" else existing_fallback

        decision = "allow"
        reason = "first_delivery"
        if hit and existing_selected:
            decision = "reject"
            reason = "duplicate_event"

        record = {
            "timestamp": ts,
            "trigger_id": canonical.get("trigger_id"),
            "decision": decision,
            "reason": reason,
            "primary_key": primary_key,
            "fallback_key": fallback_key,
            "selected_mode": selected_mode,
            "match_result": "hit" if hit else "miss",
        }
        dump_json(key_path, record)

        if hit and decision == "allow":
            entry_payload = {
                "trigger_id": canonical.get("trigger_id"),
                "created_at": ts,
                "source": canonical.get("trigger_source"),
                "decision": "allow",
            }
            if selected_tag:
                entries[selected_tag] = entry_payload
            dump_json(ledger_path, ledger)
        elif not ledger_path.exists():
            dump_json(ledger_path, ledger)

        evidence_payload = {
            "timestamp": ts,
            "status": "ok",
            "checks": {
                "match_policy_target_defined": True,
                "canonical_minimum_fields": True,
                "dedupe_keys_available": bool(primary_key or fallback_key),
                "dedupe_ambiguity": False,
            },
            "match_result": "hit" if hit else "miss",
            "dedupe_decision": decision,
            "reason": reason,
            "ledger_ref": to_rel(ledger_path, root),
        }
        dump_json(evidence_path, evidence_payload)

        output = {
            "match_result": "hit" if hit else "miss",
            "dedupe_decision": decision,
            "dedupe_key_ref": to_rel(key_path, root),
            "matcher_evidence_ref": to_rel(evidence_path, root),
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 0

    except MatcherError as exc:
        failure = {
            "timestamp": ts,
            "status": "failed",
            "reason": str(exc),
            "checks": {"fail_closed": True},
        }
        dump_json(key_path, failure)
        dump_json(evidence_path, failure)
        output = {
            "match_result": "fail",
            "dedupe_decision": "fail",
            "failure_code": "matcher_failed",
            "reason": str(exc),
            "dedupe_key_ref": to_rel(key_path, root),
            "matcher_evidence_ref": to_rel(evidence_path, root),
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MatcherError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
