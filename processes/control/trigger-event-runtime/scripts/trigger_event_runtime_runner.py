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
        default="tmp/m2-bpm-runtime/trigger-runtime-sandbox/instances",
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
            "match_policy_ref",
            "dedupe_policy_ref",
            "catchup_policy_ref",
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

        event_payload_path = evidence_dir / "event_payload.json"
        dump_json(
            event_payload_path,
            {
                "event_id": request["event_id"],
                "event_time": request["event_time"],
                "entity_type": request["entity_type"],
                "entity_id": request["entity_id"],
                "from_status": request["from_status"],
                "to_status": request["to_status"],
                "emitted_by": request.get("emitted_by", "hr"),
                "canonical_event": request.get("canonical_event", "internal.lifecycle.transitioned"),
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
                "canonical_event": request.get("canonical_event", "internal.lifecycle.transitioned"),
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
                "match_policy_ref": request["match_policy_ref"],
                "dedupe_policy_ref": request["dedupe_policy_ref"],
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

        instance_id = ""
        session_id = ""
        parent_session_id = None
        dispatch_ref = ""

        should_dispatch = match_result == "hit" and dedupe_decision == "allow"
        if should_dispatch:
            dispatch_output = evidence_dir / "p3_dispatch_output.json"
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
                "--output",
                str(dispatch_output),
            ]
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
                "catchup_policy_ref": request["catchup_policy_ref"],
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
