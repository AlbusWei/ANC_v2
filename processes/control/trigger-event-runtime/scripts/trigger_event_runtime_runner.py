#!/usr/bin/env python3
"""Executable runner for trigger-event-runtime process."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


class TriggerEventRuntimeError(RuntimeError):
    """Fail-closed runtime error."""


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
        raise TriggerEventRuntimeError("not inside a git repository")
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
        raise TriggerEventRuntimeError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TriggerEventRuntimeError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise TriggerEventRuntimeError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_cmd(cmd: List[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(root), check=False, capture_output=True, text=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run trigger-event-runtime process")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--evidence-dir",
        default="",
        help="Evidence directory path (repo-relative). Default runtime_data/execution/evidence/bpm-runtime/w3_trigger_runtime_cases/<run_id>",
    )
    parser.add_argument(
        "--instance-root",
        default="agents/control/BPM/memory/process_instances",
        help="Instance root used by process-instance-manager",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Optional run id for evidence directory naming",
    )
    return parser.parse_args()


def run_phase(
    *,
    root: Path,
    label: str,
    cmd: List[str],
    trace: List[Dict[str, Any]],
) -> Tuple[int, subprocess.CompletedProcess[str]]:
    proc = run_cmd(cmd, root)
    trace.append(
        {
            "phase": label,
            "command": cmd,
            "return_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "ts": now_iso(),
        }
    )
    return proc.returncode, proc


def parse_positive_int(raw: Any, field: str, *, minimum: int = 1) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise TriggerEventRuntimeError(f"{field}_invalid") from exc
    if value < minimum:
        raise TriggerEventRuntimeError(f"{field}_invalid")
    return value


def parse_bool_flag(raw: Any, field: str, *, default: bool = False) -> bool:
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    if isinstance(raw, str):
        normalized = raw.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off", ""}:
            return False
    raise TriggerEventRuntimeError(f"{field}_invalid")


def write_fail_closed(
    *,
    root: Path,
    output_path: Path,
    runtime_trace_path: Path,
    fail_record_path: Path,
    reason: str,
    trace: List[Dict[str, Any]],
    backfill_request_path: Path | None = None,
) -> int:
    fail_record = {
        "timestamp": now_iso(),
        "status": "failed",
        "reason": reason,
        "fail_closed": True,
    }
    dump_json(fail_record_path, fail_record)

    if backfill_request_path is not None:
        dump_json(
            backfill_request_path,
            {
                "timestamp": now_iso(),
                "status": "requested",
                "request_type": "backfill",
                "reason": reason,
            },
        )

    dump_json(
        runtime_trace_path,
        {
            "timestamp": now_iso(),
            "status": "failed",
            "phase_trace": trace,
            "fail_closed_record_ref": to_rel(fail_record_path, root),
            "backfill_request_ref": to_rel(backfill_request_path, root) if backfill_request_path else "",
        },
    )

    output = {
        "status": "failed",
        "failure_code": "trigger_event_runtime_failed",
        "reason": reason,
        "trigger_receipt_ref": "",
        "dedupe_decision": "fail",
        "runtime_trace_ref": to_rel(runtime_trace_path, root),
        "fail_closed_record_ref": to_rel(fail_record_path, root),
        "backfill_request_ref": to_rel(backfill_request_path, root) if backfill_request_path else "",
        "escalation_ref": "",
        "unmatched_event_receipt_ref": "",
    }
    dump_json(output_path, output)
    print(to_rel(output_path, root))
    return 2


def load_or_write_default(root: Path, evidence_dir: Path, ref: Any, default_name: str, payload: Dict[str, Any]) -> str:
    if isinstance(ref, str) and ref.strip():
        candidate = resolve_path(root, ref.strip())
        if not candidate.exists():
            raise TriggerEventRuntimeError(f"missing required file: {candidate}")
        return to_rel(candidate, root)

    target = evidence_dir / default_name
    dump_json(target, payload)
    return to_rel(target, root)


def ensure_ref_exists(root: Path, raw_ref: str, field_name: str) -> str:
    path = resolve_path(root, raw_ref)
    if not path.exists():
        raise TriggerEventRuntimeError(f"{field_name}_unreachable:{raw_ref}")
    return to_rel(path, root)


def route_matches(route: Dict[str, Any], request: Dict[str, Any]) -> bool:
    match_keys = [
        "event_name",
        "module",
        "trigger_source",
        "severity",
        "entity_type",
        "from_status",
        "to_status",
    ]
    for key in match_keys:
        expected = route.get(key)
        if expected is None:
            continue
        actual = request.get(key)
        if str(expected).strip() != str(actual or "").strip():
            return False
    return True


def resolve_runtime_policy_refs(root: Path, request: Dict[str, Any]) -> Dict[str, Any]:
    explicit_refs = {
        "match_policy_ref": request.get("match_policy_ref"),
        "dedupe_policy_ref": request.get("dedupe_policy_ref"),
        "catchup_policy_ref": request.get("catchup_policy_ref"),
    }
    if all(isinstance(value, str) and value.strip() for value in explicit_refs.values()):
        return {
            "matched": True,
            "source": "explicit",
            "match_policy_ref": ensure_ref_exists(root, str(explicit_refs["match_policy_ref"]).strip(), "match_policy_ref"),
            "dedupe_policy_ref": ensure_ref_exists(root, str(explicit_refs["dedupe_policy_ref"]).strip(), "dedupe_policy_ref"),
            "catchup_policy_ref": ensure_ref_exists(
                root, str(explicit_refs["catchup_policy_ref"]).strip(), "catchup_policy_ref"
            ),
            "routing_policy_ref": "",
            "route_id": "explicit",
        }

    routing_policy_raw = str(
        request.get("event_routing_policy_ref")
        or "runtime_data/private-assets/evolution/event-routing-policy.json"
    ).strip()
    routing_policy_path = resolve_path(root, routing_policy_raw)
    if not routing_policy_path.exists():
        raise TriggerEventRuntimeError(f"event_routing_policy_ref_unreachable:{routing_policy_raw}")

    routing_policy = load_json(routing_policy_path)
    routes = routing_policy.get("routes", [])
    if not isinstance(routes, list):
        raise TriggerEventRuntimeError("event_routing_policy_routes_invalid")

    chosen: Dict[str, Any] | None = None
    for item in routes:
        if not isinstance(item, dict):
            raise TriggerEventRuntimeError("event_routing_policy_route_invalid")
        if route_matches(item, request):
            chosen = item
            break

    if chosen is None:
        fallback = routing_policy.get("default_route")
        if isinstance(fallback, dict):
            chosen = fallback
        else:
            return {
                "matched": False,
                "source": "routing-policy",
                "routing_policy_ref": to_rel(routing_policy_path, root),
                "route_id": "",
            }

    match_policy_ref = str(chosen.get("match_policy_ref") or "").strip()
    dedupe_policy_ref = str(chosen.get("dedupe_policy_ref") or "").strip()
    catchup_policy_ref = str(chosen.get("catchup_policy_ref") or "").strip()
    if not (match_policy_ref and dedupe_policy_ref and catchup_policy_ref):
        raise TriggerEventRuntimeError("event_routing_policy_route_missing_policy_refs")

    return {
        "matched": True,
        "source": "routing-policy",
        "routing_policy_ref": to_rel(routing_policy_path, root),
        "route_id": str(chosen.get("route_id") or "default"),
        "match_policy_ref": ensure_ref_exists(root, match_policy_ref, "match_policy_ref"),
        "dedupe_policy_ref": ensure_ref_exists(root, dedupe_policy_ref, "dedupe_policy_ref"),
        "catchup_policy_ref": ensure_ref_exists(root, catchup_policy_ref, "catchup_policy_ref"),
    }


def write_unmatched_receipt_and_output(
    *,
    root: Path,
    output_path: Path,
    runtime_trace_path: Path,
    evidence_dir: Path,
    trace: List[Dict[str, Any]],
    request: Dict[str, Any],
    reason: str,
    dedupe_decision: str = "skip",
    policy_ref: str = "",
    match_result: str = "miss",
) -> int:
    receipt_path = evidence_dir / "unmatched_event_receipt.json"
    receipt_payload = {
        "timestamp": now_iso(),
        "status": "recorded",
        "reason": reason,
        "event_id": request.get("event_id"),
        "event_name": request.get("event_name") or request.get("canonical_event", ""),
        "module": request.get("module", ""),
        "policy_ref": policy_ref,
        "match_result": match_result,
        "dedupe_decision": dedupe_decision,
    }
    dump_json(receipt_path, receipt_payload)

    runtime_trace = {
        "timestamp": now_iso(),
        "status": "ok",
        "phase_trace": trace,
        "route_status": "unmatched",
        "unmatched_event_receipt_ref": to_rel(receipt_path, root),
    }
    dump_json(runtime_trace_path, runtime_trace)

    output = {
        "status": "ok",
        "trigger_receipt_ref": "",
        "dedupe_decision": dedupe_decision,
        "runtime_trace_ref": to_rel(runtime_trace_path, root),
        "trigger_id": "",
        "instance_id": "",
        "event_ref": "",
        "dedupe_key_ref": "",
        "dedupe_reject_log_ref": "",
        "catchup_decision": "",
        "escalation_ref": "",
        "unmatched_event_receipt_ref": to_rel(receipt_path, root),
        "fail_closed_record_ref": "",
        "backfill_request_ref": "",
    }
    dump_json(output_path, output)
    print(to_rel(output_path, root))
    return 0


def load_event_escalation_policy(root: Path, request: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, str]:
    raw_ref = str(
        request.get("event_escalation_policy_ref")
        or "runtime_data/private-assets/evolution/event-escalation-policy.json"
    ).strip()
    if not raw_ref:
        return None, ""
    policy_path = resolve_path(root, raw_ref)
    if not policy_path.exists():
        if request.get("event_escalation_policy_ref"):
            raise TriggerEventRuntimeError(f"event_escalation_policy_ref_unreachable:{raw_ref}")
        return None, ""
    payload = load_json(policy_path)
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        raise TriggerEventRuntimeError("event_escalation_policy_rules_invalid")
    return payload, to_rel(policy_path, root)


def escalation_rule_matches(rule: Dict[str, Any], request: Dict[str, Any]) -> bool:
    for key in ("event_name", "module", "trigger_source"):
        expected = rule.get(key)
        if expected is None:
            continue
        if str(expected).strip() != str(request.get(key) or "").strip():
            return False
    return True


def load_counter(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"entries": {}}
    payload = load_json(path)
    entries = payload.get("entries")
    if not isinstance(entries, dict):
        raise TriggerEventRuntimeError("escalation_counter_invalid")
    return payload


def evaluate_escalation_rule(
    *,
    root: Path,
    request: Dict[str, Any],
    rule: Dict[str, Any],
    counter_path: Path,
) -> Tuple[bool, str]:
    strategy = str(rule.get("strategy") or "immediate").strip().lower()
    if strategy == "immediate":
        return True, "rule_immediate"

    if strategy == "threshold":
        try:
            threshold = int(rule.get("threshold"))
        except (TypeError, ValueError) as exc:
            raise TriggerEventRuntimeError("escalation_threshold_invalid") from exc
        if threshold <= 0:
            raise TriggerEventRuntimeError("escalation_threshold_invalid")

        counter_key = str(
            rule.get("counter_key")
            or f"{request.get('event_name','')}|{request.get('entity_id','')}|{rule.get('rule_id','default')}"
        ).strip()
        if not counter_key:
            raise TriggerEventRuntimeError("escalation_counter_key_empty")

        counter_payload = load_counter(counter_path)
        entries = counter_payload.setdefault("entries", {})
        count_raw = entries.get(counter_key, 0)
        count = int(count_raw) if isinstance(count_raw, int) else 0
        count += 1
        entries[counter_key] = count
        counter_payload["entries"] = entries
        dump_json(counter_path, counter_payload)
        return count >= threshold, f"rule_threshold:{count}/{threshold}"

    if strategy == "sla":
        try:
            sla_minutes = int(rule.get("hold_sla_minutes") or rule.get("sla_minutes"))
        except (TypeError, ValueError) as exc:
            raise TriggerEventRuntimeError("escalation_sla_invalid") from exc
        try:
            observed_hold = int(request.get("hold_duration_minutes") or 0)
        except (TypeError, ValueError) as exc:
            raise TriggerEventRuntimeError("hold_duration_minutes_invalid") from exc
        return observed_hold > sla_minutes, f"rule_sla:{observed_hold}>{sla_minutes}"

    raise TriggerEventRuntimeError(f"unsupported_escalation_strategy:{strategy}")


def build_escalation_incident(
    *,
    request: Dict[str, Any],
    reason: str,
    severity: str,
    requested_target: str,
) -> Dict[str, Any]:
    return {
        "timestamp": now_iso(),
        "event_id": request.get("event_id"),
        "event_name": request.get("event_name") or request.get("canonical_event", ""),
        "severity": severity,
        "reason": reason,
        "requested_target": requested_target,
        "entity_id": request.get("entity_id"),
        "entity_type": request.get("entity_type"),
        "module": request.get("module", ""),
    }


def main() -> int:
    args = parse_args()
    root = repo_root()
    ts = now_iso()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    request = load_json(input_path)

    run_id = args.run_id.strip() or datetime.now(timezone.utc).strftime("tg-evt-%Y%m%dT%H%M%SZ")
    evidence_dir = resolve_path(
        root,
        args.evidence_dir.strip() or f"runtime_data/execution/evidence/bpm-runtime/w3_trigger_runtime_cases/{run_id}",
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    runtime_trace_path = evidence_dir / "runtime_trace.json"
    fail_record_path = evidence_dir / "fail_closed_record.json"
    backfill_request_path = evidence_dir / "backfill_request.json"

    trace: List[Dict[str, Any]] = []

    try:
        required = [
            "event_id",
            "event_time",
            "entity_type",
            "entity_id",
            "from_status",
            "to_status",
        ]
        missing = [field for field in required if field not in request]
        if missing:
            raise TriggerEventRuntimeError(f"missing required input fields: {','.join(missing)}")

        transition_evidence_ref = request.get("transition_evidence_ref") or request.get("evidence_ref")
        if not isinstance(transition_evidence_ref, str) or not transition_evidence_ref.strip():
            return write_fail_closed(
                root=root,
                output_path=output_path,
                runtime_trace_path=runtime_trace_path,
                fail_record_path=fail_record_path,
                reason="missing_transition_evidence_ref",
                trace=trace,
                backfill_request_path=backfill_request_path,
            )
        transition_evidence = resolve_path(root, transition_evidence_ref.strip())
        if not transition_evidence.exists():
            return write_fail_closed(
                root=root,
                output_path=output_path,
                runtime_trace_path=runtime_trace_path,
                fail_record_path=fail_record_path,
                reason="transition_evidence_unreachable",
                trace=trace,
                backfill_request_path=backfill_request_path,
            )

        policy_resolution = resolve_runtime_policy_refs(root, request)
        if not policy_resolution.get("matched"):
            return write_unmatched_receipt_and_output(
                root=root,
                output_path=output_path,
                runtime_trace_path=runtime_trace_path,
                evidence_dir=evidence_dir,
                trace=trace,
                request=request,
                reason="route_unmatched",
                dedupe_decision="skip",
                policy_ref=str(policy_resolution.get("routing_policy_ref") or ""),
                match_result="miss",
            )

        match_policy_ref = str(policy_resolution["match_policy_ref"])
        dedupe_policy_ref = str(policy_resolution["dedupe_policy_ref"])
        catchup_policy_ref = str(policy_resolution["catchup_policy_ref"])

        event_payload_path = evidence_dir / "event_payload.json"
        dump_json(
            event_payload_path,
            {
                "event_id": request["event_id"],
                "event_name": request.get("event_name", ""),
                "event_time": request["event_time"],
                "module": request.get("module", ""),
                "severity": request.get("severity", "info"),
                "entity_type": request["entity_type"],
                "entity_id": request["entity_id"],
                "from_status": request["from_status"],
                "to_status": request["to_status"],
                "emitted_by": request.get("emitted_by", "hr"),
                "owner_agent_id": request.get("owner_agent_id", "owner"),
                "canonical_event": request.get("canonical_event") or request.get("event_name") or "internal.lifecycle.transitioned",
                "transition_evidence_ref": transition_evidence_ref,
            },
        )

        normalizer_input = evidence_dir / "p1_input.json"
        normalizer_output = evidence_dir / "p1_output.json"
        canonical_output = evidence_dir / "p1_canonical.json"
        normalizer_report = evidence_dir / "p1_report.json"

        dump_json(
            normalizer_input,
            {
                "trigger_type": "event",
                "trigger_source": request.get("trigger_source", "lifecycle"),
                "payload_ref": to_rel(event_payload_path, root),
                "received_at": request.get("received_at", ts),
                "canonical_event": request.get("canonical_event")
                or request.get("event_name")
                or "internal.lifecycle.transitioned",
            },
        )

        normalizer_cmd = [
            sys.executable,
            "skills/system/trigger-ingress-normalizer/scripts/trigger_ingress_normalizer_runner.py",
            "--input",
            to_rel(normalizer_input, root),
            "--output",
            to_rel(normalizer_output, root),
            "--canonical",
            to_rel(canonical_output, root),
            "--report",
            to_rel(normalizer_report, root),
        ]
        rc, _ = run_phase(root=root, label="p1-normalize", cmd=normalizer_cmd, trace=trace)
        if rc != 0:
            return write_fail_closed(
                root=root,
                output_path=output_path,
                runtime_trace_path=runtime_trace_path,
                fail_record_path=fail_record_path,
                reason="p1_normalizer_failed",
                trace=trace,
                backfill_request_path=backfill_request_path,
            )

        p1_output = load_json(normalizer_output)
        canonical_ref = p1_output.get("canonical_trigger_ref")
        trigger_id = p1_output.get("trigger_id")
        if not isinstance(canonical_ref, str) or not canonical_ref.strip():
            raise TriggerEventRuntimeError("p1 output missing canonical_trigger_ref")
        if not isinstance(trigger_id, str) or not trigger_id.strip():
            raise TriggerEventRuntimeError("p1 output missing trigger_id")

        matcher_input = evidence_dir / "p2_input.json"
        matcher_output = evidence_dir / "p2_output.json"
        dedupe_key = evidence_dir / "p2_dedupe_key.json"
        matcher_evidence = evidence_dir / "p2_matcher_evidence.json"

        dedupe_ledger_path = resolve_path(root, request.get("dedupe_ledger_ref") or to_rel(evidence_dir / "dedupe_ledger.json", root))
        dedupe_ledger_path.parent.mkdir(parents=True, exist_ok=True)

        dump_json(
            matcher_input,
            {
                "canonical_trigger_ref": canonical_ref,
                "match_policy_ref": match_policy_ref,
                "dedupe_policy_ref": dedupe_policy_ref,
            },
        )

        matcher_cmd = [
            sys.executable,
            "skills/system/trigger-matcher-dedupe/scripts/trigger_matcher_dedupe_runner.py",
            "--input",
            to_rel(matcher_input, root),
            "--output",
            to_rel(matcher_output, root),
            "--dedupe-key",
            to_rel(dedupe_key, root),
            "--evidence",
            to_rel(matcher_evidence, root),
            "--ledger",
            to_rel(dedupe_ledger_path, root),
        ]
        rc, _ = run_phase(root=root, label="p2-match-dedupe", cmd=matcher_cmd, trace=trace)
        if rc != 0:
            return write_fail_closed(
                root=root,
                output_path=output_path,
                runtime_trace_path=runtime_trace_path,
                fail_record_path=fail_record_path,
                reason="p2_matcher_failed",
                trace=trace,
            )

        p2_output = load_json(matcher_output)
        match_result = str(p2_output.get("match_result") or "")
        dedupe_decision = str(p2_output.get("dedupe_decision") or "")
        if match_result not in {"hit", "miss"}:
            raise TriggerEventRuntimeError("invalid_match_result")
        if dedupe_decision not in {"allow", "reject"}:
            raise TriggerEventRuntimeError("invalid_dedupe_decision")

        if match_result == "miss":
            return write_unmatched_receipt_and_output(
                root=root,
                output_path=output_path,
                runtime_trace_path=runtime_trace_path,
                evidence_dir=evidence_dir,
                trace=trace,
                request=request,
                reason="route_unmatched",
                dedupe_decision=dedupe_decision,
                policy_ref=str(policy_resolution.get("routing_policy_ref") or ""),
                match_result=match_result,
            )

        instance_id = ""
        session_id = ""
        parent_session_id = None
        dispatch_ref = ""

        should_dispatch = match_result == "hit" and dedupe_decision == "allow"
        if should_dispatch:
            dispatch_output = evidence_dir / "p3_dispatch_output.json"
            trigger_source = str(request.get("trigger_source") or "").strip().lower()
            dispatch_default = trigger_source == "platform-hook"
            dispatch_openclaw = parse_bool_flag(
                request.get("dispatch_openclaw"),
                "dispatch_openclaw",
                default=dispatch_default,
            )
            reset_openclaw_session = parse_bool_flag(
                request.get("reset_openclaw_session"),
                "reset_openclaw_session",
                default=dispatch_openclaw,
            )
            strict_session_match = parse_bool_flag(
                request.get("strict_session_match"),
                "strict_session_match",
                default=dispatch_openclaw,
            )
            dispatch_openclaw_bin = str(request.get("dispatch_openclaw_bin") or "openclaw").strip() or "openclaw"
            openclaw_stall_threshold = parse_positive_int(
                request.get("dispatch_openclaw_stall_threshold_seconds", 900),
                "dispatch_openclaw_stall_threshold_seconds",
                minimum=900,
            )
            openclaw_probe_interval = parse_positive_int(
                request.get("dispatch_openclaw_probe_interval_seconds", 60),
                "dispatch_openclaw_probe_interval_seconds",
                minimum=5,
            )
            dispatch_cmd = [
                sys.executable,
                "skills/system/process-instance-manager/scripts/process_instance_runner.py",
                "start",
                "--process-id",
                str(request.get("target_process_id") or "development-process"),
                "--phase-id",
                str(request.get("target_phase_id") or "p1"),
                "--instance-root",
                str(resolve_path(root, args.instance_root)),
                "--initiated-by",
                "bpm",
                "--input-ref",
                canonical_ref,
                "--openclaw-bin",
                dispatch_openclaw_bin,
                "--openclaw-stall-threshold-seconds",
                str(openclaw_stall_threshold),
                "--openclaw-probe-interval-seconds",
                str(openclaw_probe_interval),
                "--output",
                str(dispatch_output),
            ]
            if dispatch_openclaw:
                dispatch_cmd.append("--execute-openclaw")
                if reset_openclaw_session:
                    dispatch_cmd.append("--reset-openclaw-session")
                if strict_session_match:
                    dispatch_cmd.append("--strict-session-match")
            rc, _ = run_phase(root=root, label="p3-dispatch-instance", cmd=dispatch_cmd, trace=trace)
            if rc != 0:
                return write_fail_closed(
                    root=root,
                    output_path=output_path,
                    runtime_trace_path=runtime_trace_path,
                    fail_record_path=fail_record_path,
                    reason="p3_dispatch_failed",
                    trace=trace,
                )

            dispatch_payload = load_json(dispatch_output)
            instance_id = str(dispatch_payload.get("instance_id") or "")
            if not instance_id:
                raise TriggerEventRuntimeError("dispatch output missing instance_id")
            dispatch_ref = to_rel(dispatch_output, root)

            binding_ref = dispatch_payload.get("session_binding_ref")
            if not isinstance(binding_ref, str) or not binding_ref.strip():
                raise TriggerEventRuntimeError("dispatch output missing session_binding_ref")
            binding = load_json(resolve_path(root, binding_ref))
            session_id = str(binding.get("session_id") or "")
            parent_session_id = binding.get("parent_session_id")
            if not session_id:
                raise TriggerEventRuntimeError("dispatch session_id missing")

            # Fail-closed: reject cross-instance session reuse.
            session_ledger = evidence_dir / "session_ledger.json"
            ledger = load_json(session_ledger) if session_ledger.exists() else {"session_to_instance": {}}
            mapping = ledger.get("session_to_instance")
            if not isinstance(mapping, dict):
                raise TriggerEventRuntimeError("session_ledger_invalid")
            if session_id in mapping and mapping[session_id] != instance_id:
                raise TriggerEventRuntimeError("cross_instance_session_reuse_detected")
            mapping[session_id] = instance_id
            ledger["session_to_instance"] = mapping
            dump_json(session_ledger, ledger)
        else:
            instance_id = f"virtual-{trigger_id}"

        evidence_payload = evidence_dir / "p4_evidence_payload.json"
        dump_json(
            evidence_payload,
            {
                "timestamp": now_iso(),
                "actor": "bpm",
                "trigger_id": trigger_id,
                "instance_id": instance_id,
                "match_result": match_result,
                "dedupe_decision": dedupe_decision,
                "session_id": session_id,
                "parent_session_id": parent_session_id,
                "dispatch_ref": dispatch_ref,
            },
        )

        evidence_input = evidence_dir / "p4_input.json"
        evidence_output = evidence_dir / "p4_output.json"
        evidence_receipt = evidence_dir / "p4_trigger_receipt.json"
        evidence_index = evidence_dir / "evidence_index.jsonl"
        traceability_link = evidence_dir / "p4_traceability.json"

        decision_for_receipt = "reject" if dedupe_decision == "reject" else "hit"
        dump_json(
            evidence_input,
            {
                "trigger_id": trigger_id,
                "instance_id": instance_id,
                "decision": decision_for_receipt,
                "evidence_payload_ref": to_rel(evidence_payload, root),
            },
        )

        evidence_cmd = [
            sys.executable,
            "skills/system/evidence-recorder/scripts/evidence_recorder_runner.py",
            "--input",
            to_rel(evidence_input, root),
            "--output",
            to_rel(evidence_output, root),
            "--receipt",
            to_rel(evidence_receipt, root),
            "--index",
            to_rel(evidence_index, root),
            "--trace",
            to_rel(traceability_link, root),
        ]
        rc, _ = run_phase(root=root, label="p4-record-evidence", cmd=evidence_cmd, trace=trace)
        if rc != 0:
            return write_fail_closed(
                root=root,
                output_path=output_path,
                runtime_trace_path=runtime_trace_path,
                fail_record_path=fail_record_path,
                reason="p4_evidence_record_failed",
                trace=trace,
            )

        p4_output = load_json(evidence_output)
        trigger_receipt_ref = p4_output.get("trigger_receipt_ref")
        if not isinstance(trigger_receipt_ref, str) or not trigger_receipt_ref.strip():
            raise TriggerEventRuntimeError("p4 output missing trigger_receipt_ref")

        missed_run_ref = load_or_write_default(
            root,
            evidence_dir,
            request.get("missed_run_ref"),
            "p5_missed_run.json",
            {
                "missed": bool(request.get("missed", False)),
                "expected_run_at": request.get("expected_run_at", now_iso()),
            },
        )
        trigger_policy_ref = load_or_write_default(
            root,
            evidence_dir,
            request.get("trigger_policy_ref"),
            "p5_trigger_policy.json",
            {
                "trigger_type": "event",
                "delivery_policy": "event-driven",
            },
        )
        runtime_state_ref = load_or_write_default(
            root,
            evidence_dir,
            request.get("runtime_state_ref"),
            "p5_runtime_state.json",
            {
                "observed_at": now_iso(),
                "risk_level": request.get("risk_level", "low"),
                "trigger_type": "event",
            },
        )

        catchup_input = evidence_dir / "p5_input.json"
        catchup_output = evidence_dir / "p5_output.json"
        catchup_run = evidence_dir / "p5_catchup_run.json"
        catchup_reason = evidence_dir / "p5_reason.json"

        dump_json(
            catchup_input,
            {
                "missed_run_ref": missed_run_ref,
                "catchup_policy_ref": catchup_policy_ref,
                "trigger_policy_ref": trigger_policy_ref,
                "runtime_state_ref": runtime_state_ref,
            },
        )

        catchup_cmd = [
            sys.executable,
            "skills/system/catchup-scheduler/scripts/catchup_scheduler_runner.py",
            "--input",
            to_rel(catchup_input, root),
            "--output",
            to_rel(catchup_output, root),
            "--run",
            to_rel(catchup_run, root),
            "--reason",
            to_rel(catchup_reason, root),
        ]
        rc, _ = run_phase(root=root, label="p5-backfill-catchup", cmd=catchup_cmd, trace=trace)
        if rc != 0:
            return write_fail_closed(
                root=root,
                output_path=output_path,
                runtime_trace_path=runtime_trace_path,
                fail_record_path=fail_record_path,
                reason="p5_catchup_failed",
                trace=trace,
            )

        p5_output = load_json(catchup_output)

        dedupe_reject_log_ref = ""
        if dedupe_decision == "reject":
            dedupe_reject_log = evidence_dir / "dedupe_reject_log.json"
            dump_json(
                dedupe_reject_log,
                {
                    "timestamp": now_iso(),
                    "trigger_id": trigger_id,
                    "dedupe_key_ref": p2_output.get("dedupe_key_ref"),
                    "reason": "duplicate event rejected",
                },
            )
            dedupe_reject_log_ref = to_rel(dedupe_reject_log, root)

        escalation_ref = ""
        escalation_decision = "skip"
        escalation_rule_id = ""
        escalation_policy, escalation_policy_ref = load_event_escalation_policy(root, request)
        if escalation_policy is not None:
            rules = escalation_policy.get("rules", [])
            if not isinstance(rules, list):
                raise TriggerEventRuntimeError("event_escalation_policy_rules_invalid")

            counter_ref = str(
                request.get("escalation_counter_ref")
                or to_rel(evidence_dir / "p6_escalation_counter.json", root)
            ).strip()
            counter_path = resolve_path(root, counter_ref)
            counter_path.parent.mkdir(parents=True, exist_ok=True)

            for rule in rules:
                if not isinstance(rule, dict):
                    raise TriggerEventRuntimeError("event_escalation_rule_invalid")
                if not escalation_rule_matches(rule, request):
                    continue

                should_escalate, eval_reason = evaluate_escalation_rule(
                    root=root,
                    request=request,
                    rule=rule,
                    counter_path=counter_path,
                )
                if not should_escalate:
                    continue

                chain_policy_raw = str(
                    rule.get("escalation_chain_policy_ref")
                    or escalation_policy.get("escalation_chain_policy_ref")
                    or ""
                ).strip()
                if not chain_policy_raw:
                    raise TriggerEventRuntimeError("missing_escalation_chain_policy_ref")
                chain_policy_ref = ensure_ref_exists(root, chain_policy_raw, "escalation_chain_policy_ref")

                incident_path = evidence_dir / "p6_incident.json"
                incident_payload = build_escalation_incident(
                    request=request,
                    reason=str(rule.get("reason_template") or eval_reason),
                    severity=str(rule.get("severity") or "high"),
                    requested_target="",
                )
                dump_json(incident_path, incident_payload)

                escalation_input = evidence_dir / "p6_input.json"
                escalation_output = evidence_dir / "p6_output.json"
                escalation_record = evidence_dir / "p6_record.json"
                dump_json(
                    escalation_input,
                    {
                        "incident_ref": to_rel(incident_path, root),
                        "escalation_policy_ref": chain_policy_ref,
                        "current_owner": str(request.get("owner_agent_id") or "owner"),
                        "evidence_ref": trigger_receipt_ref,
                    },
                )

                escalation_cmd = [
                    sys.executable,
                    "skills/system/escalation-handler/scripts/escalation_handler_runner.py",
                    "--input",
                    to_rel(escalation_input, root),
                    "--output",
                    to_rel(escalation_output, root),
                    "--record",
                    to_rel(escalation_record, root),
                ]
                rc, _ = run_phase(root=root, label="p6-escalate-runtime-anomaly", cmd=escalation_cmd, trace=trace)
                if rc != 0:
                    return write_fail_closed(
                        root=root,
                        output_path=output_path,
                        runtime_trace_path=runtime_trace_path,
                        fail_record_path=fail_record_path,
                        reason="p6_escalation_failed",
                        trace=trace,
                    )

                escalation_payload = load_json(escalation_output)
                escalation_ref = str(escalation_payload.get("escalation_ref") or "").strip()
                if not escalation_ref:
                    raise TriggerEventRuntimeError("p6_missing_escalation_ref")
                escalation_decision = str(escalation_payload.get("escalation_decision") or "escalate")
                escalation_rule_id = str(rule.get("rule_id") or "")
                break

        runtime_trace = {
            "timestamp": now_iso(),
            "status": "ok",
            "trigger_id": trigger_id,
            "instance_id": instance_id,
            "session_id": session_id,
            "parent_session_id": parent_session_id,
            "match_result": match_result,
            "dedupe_decision": dedupe_decision,
            "catchup_decision": p5_output.get("catchup_decision"),
            "escalation_decision": escalation_decision,
            "escalation_ref": escalation_ref,
            "escalation_rule_id": escalation_rule_id,
            "routing_policy_ref": str(policy_resolution.get("routing_policy_ref") or ""),
            "route_id": str(policy_resolution.get("route_id") or ""),
            "escalation_policy_ref": escalation_policy_ref,
            "phase_trace": trace,
        }
        dump_json(runtime_trace_path, runtime_trace)

        output = {
            "status": "ok",
            "trigger_receipt_ref": trigger_receipt_ref,
            "dedupe_decision": dedupe_decision,
            "runtime_trace_ref": to_rel(runtime_trace_path, root),
            "trigger_id": trigger_id,
            "instance_id": instance_id,
            "event_ref": to_rel(event_payload_path, root),
            "dedupe_key_ref": p2_output.get("dedupe_key_ref", ""),
            "dedupe_reject_log_ref": dedupe_reject_log_ref,
            "catchup_decision": p5_output.get("catchup_decision", ""),
            "escalation_ref": escalation_ref,
            "unmatched_event_receipt_ref": "",
            "fail_closed_record_ref": "",
            "backfill_request_ref": "",
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 0

    except TriggerEventRuntimeError as exc:
        return write_fail_closed(
            root=root,
            output_path=output_path,
            runtime_trace_path=runtime_trace_path,
            fail_record_path=fail_record_path,
            reason=str(exc),
            trace=trace,
        )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except TriggerEventRuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
