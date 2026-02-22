#!/usr/bin/env python3
import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict


def load_json(path: Path, default=None):
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_iso_utc(value: str):
    if not value:
        return None
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def compute_log_delta(current_log: str, previous_log: str) -> Dict[str, Any]:
    return {
        "log_delta": len(current_log) > len(previous_log),
        "current_log_bytes": len(current_log),
        "previous_log_bytes": len(previous_log),
    }


def compute_phase_progress(current_state: Dict[str, Any], previous_state: Dict[str, Any]) -> Dict[str, Any]:
    current_phase = str(current_state.get("phase_progress", current_state.get("state", ""))).strip()
    previous_phase = str(previous_state.get("phase_progress", previous_state.get("state", ""))).strip()
    current_seq = int(current_state.get("phase_index", current_state.get("progress_index", 0)) or 0)
    previous_seq = int(previous_state.get("phase_index", previous_state.get("progress_index", 0)) or 0)
    progressed = False
    if current_seq > previous_seq:
        progressed = True
    elif current_phase and previous_phase and current_phase != previous_phase:
        progressed = True
    return {
        "phase_progress": progressed,
        "current_phase": current_phase,
        "previous_phase": previous_phase,
        "current_phase_index": current_seq,
        "previous_phase_index": previous_seq,
    }


def compute_output_heartbeat(hold_case: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
    heartbeat_flag = hold_case.get("output_heartbeat")
    if isinstance(heartbeat_flag, bool):
        return {"output_heartbeat": heartbeat_flag, "heartbeat_source": "bool_flag"}

    now = dt.datetime.now(dt.timezone.utc)
    max_age_seconds = int(policy.get("heartbeat_max_age_seconds", 600))
    heartbeat_at = (
        hold_case.get("last_output_heartbeat_at")
        or hold_case.get("heartbeat_at")
        or hold_case.get("last_heartbeat_at")
        or ""
    )
    parsed = parse_iso_utc(str(heartbeat_at))
    if parsed is None:
        return {"output_heartbeat": False, "heartbeat_source": "missing_timestamp"}
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    age_seconds = (now - parsed).total_seconds()
    return {
        "output_heartbeat": age_seconds <= max_age_seconds,
        "heartbeat_source": "timestamp",
        "heartbeat_at": parsed.isoformat(),
        "heartbeat_age_seconds": age_seconds,
        "heartbeat_max_age_seconds": max_age_seconds,
    }


def choose_action(log_delta: bool, phase_progress: bool, output_heartbeat: bool, policy: Dict[str, Any]) -> str:
    if log_delta and phase_progress and output_heartbeat:
        return "continue"
    if output_heartbeat and (log_delta or phase_progress):
        return "retry"
    if log_delta or phase_progress:
        return "debug"
    return str(policy.get("on_no_progress", "fail")).strip() or "fail"


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify hold triage action")
    parser.add_argument("--hold-case", required=True)
    parser.add_argument("--runtime-log", required=True)
    parser.add_argument("--execution-state", required=True)
    parser.add_argument("--triage-policy", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--previous-runtime-log", default="")
    parser.add_argument("--previous-execution-state", default="")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    signals_ref = out_dir / "progress_signals.json"
    report_ref = out_dir / "triage_report.json"
    action_ref = out_dir / "action_execution.json"

    try:
        hold_case = load_json(Path(args.hold_case))
        runtime_log = read_text(Path(args.runtime_log))
        execution_state = load_json(Path(args.execution_state), default={})
        policy = load_json(Path(args.triage_policy))

        previous_runtime_log = read_text(Path(args.previous_runtime_log)) if args.previous_runtime_log else ""
        previous_execution_state = (
            load_json(Path(args.previous_execution_state), default={}) if args.previous_execution_state else {}
        )

        allowed_actions = set(policy.get("allowed_actions", ["continue", "retry", "debug", "fail"]))

        log_signal = compute_log_delta(runtime_log, previous_runtime_log)
        phase_signal = compute_phase_progress(execution_state, previous_execution_state)
        heartbeat_signal = compute_output_heartbeat(hold_case, policy)

        log_delta = bool(log_signal["log_delta"])
        phase_progress = bool(phase_signal["phase_progress"])
        output_heartbeat = bool(heartbeat_signal["output_heartbeat"])

        triage_action = choose_action(log_delta, phase_progress, output_heartbeat, policy)
        if triage_action not in allowed_actions:
            triage_action = "fail"

        gate_decision = "pass" if triage_action != "fail" else "fail"
        reasons = [
            "triage_action=%s" % triage_action,
            "log_delta=%s" % log_delta,
            "phase_progress=%s" % phase_progress,
            "output_heartbeat=%s" % output_heartbeat,
        ]
        if triage_action == "fail":
            reasons.append("missing_progress_signals")

        signals_payload = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "log_signal": log_signal,
            "phase_signal": phase_signal,
            "heartbeat_signal": heartbeat_signal,
            "log_delta": log_delta,
            "phase_progress": phase_progress,
            "output_heartbeat": output_heartbeat,
        }
        signals_ref.write_text(json.dumps(signals_payload, indent=2), encoding="utf-8")

        report_payload = {
            "triage_action": triage_action,
            "gate_decision": gate_decision,
            "reasons": reasons,
            "progress_signals_ref": str(signals_ref),
            "policy_ref": args.triage_policy,
            "runtime_refs": {
                "current_runtime_log_ref": args.runtime_log,
                "current_execution_state_ref": args.execution_state,
                "previous_runtime_log_ref": args.previous_runtime_log,
                "previous_execution_state_ref": args.previous_execution_state,
            },
        }
        report_ref.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

        action_payload = {
            "triage_action": triage_action,
            "executed": triage_action != "fail",
            "next_step": triage_action,
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        action_ref.write_text(json.dumps(action_payload, indent=2), encoding="utf-8")

        output = {
            "progress_signals_ref": str(signals_ref),
            "triage_action": triage_action,
            "triage_report_ref": str(report_ref),
            "action_execution_ref": str(action_ref),
            "gate_decision": gate_decision,
            "evidence_ref": str(out_dir),
            "reasons": reasons,
        }
        print(json.dumps(output, ensure_ascii=True))
        return 0 if gate_decision == "pass" else 40
    except Exception as exc:
        output = {
            "progress_signals_ref": str(signals_ref),
            "triage_action": "fail",
            "triage_report_ref": str(report_ref),
            "action_execution_ref": str(action_ref),
            "gate_decision": "fail",
            "evidence_ref": str(out_dir),
            "reasons": ["exception", str(exc)],
        }
        report_ref.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(json.dumps(output, ensure_ascii=True))
        return 40


if __name__ == "__main__":
    raise SystemExit(main())
