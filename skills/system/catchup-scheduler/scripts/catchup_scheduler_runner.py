#!/usr/bin/env python3
"""Executable runner for sys.bpm.catchup-scheduler."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class CatchupSchedulerError(RuntimeError):
    """Unexpected catchup scheduler failure."""


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
        raise CatchupSchedulerError("not inside a git repository")
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
        raise CatchupSchedulerError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CatchupSchedulerError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CatchupSchedulerError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_ts(raw: Any, field: str) -> datetime:
    if not isinstance(raw, str) or not raw.strip():
        raise CatchupSchedulerError(f"{field} must be non-empty RFC3339 string")
    text = raw.strip()
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        stamp = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CatchupSchedulerError(f"invalid timestamp for {field}: {text}") from exc
    if stamp.tzinfo is None:
        raise CatchupSchedulerError(f"{field} must include timezone")
    return stamp.astimezone(timezone.utc)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute dynamic catchup scheduling")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--run", required=True, help="Catchup run artifact path")
    parser.add_argument("--reason", required=True, help="Catchup reason artifact path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    ts = now_iso()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    run_path = resolve_path(root, args.run)
    reason_path = resolve_path(root, args.reason)

    request = load_json(input_path)

    try:
        catchup_policy_ref = request.get("catchup_policy_ref")
        trigger_policy_ref = request.get("trigger_policy_ref")
        runtime_state_ref = request.get("runtime_state_ref")
        missed_run_ref = request.get("missed_run_ref")

        if not isinstance(catchup_policy_ref, str) or not catchup_policy_ref.strip():
            raise CatchupSchedulerError("missing_catchup_policy_ref")
        if not isinstance(trigger_policy_ref, str) or not trigger_policy_ref.strip():
            raise CatchupSchedulerError("missing_trigger_policy_ref")
        if not isinstance(runtime_state_ref, str) or not runtime_state_ref.strip():
            raise CatchupSchedulerError("missing_runtime_state_ref")
        if not isinstance(missed_run_ref, str) or not missed_run_ref.strip():
            raise CatchupSchedulerError("missing_missed_run_ref")

        catchup_policy = load_json(resolve_path(root, catchup_policy_ref.strip()))
        _trigger_policy = load_json(resolve_path(root, trigger_policy_ref.strip()))
        runtime_state = load_json(resolve_path(root, runtime_state_ref.strip()))
        missed_run = load_json(resolve_path(root, missed_run_ref.strip()))

        risk_level = str(runtime_state.get("risk_level") or "").lower()
        if risk_level not in {"low", "medium", "high"}:
            raise CatchupSchedulerError("runtime_state.risk_level must be low|medium|high")

        window_cfg = catchup_policy.get("window_minutes_by_risk")
        if not isinstance(window_cfg, dict):
            raise CatchupSchedulerError("catchup_policy.window_minutes_by_risk missing")
        window_value = window_cfg.get(risk_level)
        if not isinstance(window_value, int) or window_value <= 0:
            raise CatchupSchedulerError("dynamic_window_not_evaluable")

        enabled = missed_run.get("missed")
        if enabled is not True:
            reason_payload = {
                "timestamp": ts,
                "decision": "skip",
                "reason": "no_missed_run",
                "window_minutes": window_value,
            }
            dump_json(reason_path, reason_payload)
            output = {
                "catchup_decision": "skip",
                "catchup_run_ref": "",
                "catchup_reason_ref": to_rel(reason_path, root),
                "escalation_hint": "",
            }
            dump_json(output_path, output)
            print(to_rel(output_path, root))
            return 0

        expected_run_at = parse_ts(missed_run.get("expected_run_at"), "expected_run_at")
        observed_at = parse_ts(runtime_state.get("observed_at") or ts, "observed_at")
        lag_minutes = int((observed_at - expected_run_at).total_seconds() // 60)

        if lag_minutes < 0:
            decision = "skip"
            reason = "expected_run_in_future"
            escalation_hint = ""
            run_ref = ""
        elif lag_minutes <= window_value:
            decision = "run"
            reason = "within_dynamic_window"
            escalation_hint = ""
            run_payload = {
                "timestamp": ts,
                "status": "scheduled",
                "expected_run_at": expected_run_at.isoformat().replace("+00:00", "Z"),
                "observed_at": observed_at.isoformat().replace("+00:00", "Z"),
                "lag_minutes": lag_minutes,
                "window_minutes": window_value,
            }
            dump_json(run_path, run_payload)
            run_ref = to_rel(run_path, root)
        else:
            decision = "escalate"
            reason = "outside_dynamic_window"
            escalation_hint = (
                f"catchup lag {lag_minutes}m exceeds window {window_value}m for risk={risk_level}; escalate owner"
            )
            run_ref = ""

        reason_payload = {
            "timestamp": ts,
            "decision": decision,
            "reason": reason,
            "lag_minutes": lag_minutes,
            "window_minutes": window_value,
            "risk_level": risk_level,
        }
        dump_json(reason_path, reason_payload)

        output = {
            "catchup_decision": decision,
            "catchup_run_ref": run_ref,
            "catchup_reason_ref": to_rel(reason_path, root),
            "escalation_hint": escalation_hint,
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 0

    except CatchupSchedulerError as exc:
        failure = {
            "timestamp": ts,
            "status": "failed",
            "reason": str(exc),
            "fail_closed": True,
        }
        dump_json(reason_path, failure)
        output = {
            "catchup_decision": "fail",
            "catchup_run_ref": "",
            "catchup_reason_ref": to_rel(reason_path, root),
            "escalation_hint": "",
            "failure_code": "catchup_scheduler_failed",
            "reason": str(exc),
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CatchupSchedulerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
