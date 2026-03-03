#!/usr/bin/env python3
"""refactor 运行级协作骨架执行器（phase 分发优先版）。

说明：
1. 本 runner 优先验证 BPM 对多 phase 的真实 openclaw 分发能力。
2. 本轮先产出协作骨架证据与阶段输出引用，不内联执行所有子流程 runner。
3. 每个 phase 都通过 process-instance-manager 创建实例并可选真实分发。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class RefactorError(RuntimeError):
    """Fail-closed runtime error for refactor."""


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
        raise RefactorError("not inside a git repository")
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
        raise RefactorError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RefactorError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RefactorError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_cmd(cmd: List[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(root), check=False, capture_output=True, text=True)


ALLOWED_EVENT_NAMES = {
    "m1.gate.failed",
    "m1.gate.hold",
    "m1.gate.pass",
    "m3.implementation.failed",
    "m3.implementation.completed",
    "m4.lifecycle.transition.approved",
    "m4.lifecycle.transition.rejected",
    "m4.lifecycle.rollback.executed",
    "m5.proposal.rejected",
    "m5.proposal.accepted",
    "asset.health.degraded",
    "asset.health.critical",
}


def validate_domain_event(event_payload: Dict[str, Any]) -> None:
    required = [
        "contract_version",
        "event_id",
        "event_name",
        "event_time",
        "module",
        "trigger_source",
        "severity",
        "evidence_ref",
        "owner_agent_id",
        "dedupe_key",
    ]
    missing = [key for key in required if not str(event_payload.get(key) or "").strip()]
    if missing:
        raise RefactorError(f"domain_event_missing_fields:{','.join(missing)}")
    if event_payload.get("contract_version") != "0.1.0":
        raise RefactorError("domain_event_contract_version_invalid")
    if str(event_payload.get("event_name")) not in ALLOWED_EVENT_NAMES:
        raise RefactorError("domain_event_name_invalid")
    if str(event_payload.get("module")) not in {"m1", "m3", "m4", "m5", "runtime-monitor"}:
        raise RefactorError("domain_event_module_invalid")
    if str(event_payload.get("trigger_source")) not in {"platform-hook", "domain-hook", "heartbeat", "cron"}:
        raise RefactorError("domain_event_trigger_source_invalid")
    if str(event_payload.get("severity")) not in {"info", "warning", "critical"}:
        raise RefactorError("domain_event_severity_invalid")
    if not str(event_payload.get("asset_ref") or event_payload.get("target_product_id") or "").strip():
        raise RefactorError("domain_event_target_missing")


def emit_domain_event(
    *,
    root: Path,
    process_id: str,
    event_name: str,
    severity: str,
    evidence_ref: str,
    owner_agent_id: str,
    asset_ref: str,
) -> str:
    timestamp = now_iso()
    bucket = timestamp[:16].replace("-", "").replace(":", "").replace("T", "T")
    event_id = f"{event_name.replace('.', '-')}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{process_id}"
    payload = {
        "contract_version": "0.1.0",
        "event_id": event_id,
        "event_name": event_name,
        "event_time": timestamp,
        "module": "m3",
        "trigger_source": "domain-hook",
        "severity": severity,
        "asset_ref": asset_ref,
        "evidence_ref": evidence_ref,
        "owner_agent_id": owner_agent_id,
        "dedupe_key": f"{event_name}|{asset_ref}|{bucket}",
        "window_bucket": bucket,
        "trace": {
            "process_id": process_id,
            "emitted_by_runner": "refactor",
        },
    }
    validate_domain_event(payload)
    event_path = root / "runtime_data/evolution/events" / f"{event_id}.json"
    dump_json(event_path, payload)
    return to_rel(event_path, root)


PHASE_OUTPUT_FIELDS: Dict[str, List[str]] = {
    "p1": ["objective_ref", "scope_baseline_ref"],
    "p2": ["spec_ref"],
    "p3": ["test_plan_ref", "preparation_bundle_ref"],
    "p4": ["implementation_ref", "candidate_artifacts_ref"],
    "p5": ["final_gate_verdict_ref"],
    "p6": ["lifecycle_transition_ref", "registry_sync_ref"],
}


PHASE_INPUT_KEYS: Dict[str, List[str]] = {
    "p1": ["objective_context_ref", "tech_debt_ref", "target_asset_ref"],
    "p2": ["objective_ref", "scope_baseline_ref"],
    "p3": ["spec_ref", "superpower_ref"],
    "p4": ["spec_ref", "test_plan_ref", "preparation_bundle_ref"],
    "p5": ["candidate_artifacts_ref", "implementation_ref", "preparation_bundle_ref", "superpower_ref"],
    "p6": ["final_gate_verdict_ref", "target_asset_ref", "lifecycle_target", "superpower_ref"],
}


def gather_phase_inputs(
    phase_id: str,
    request: Dict[str, Any],
    produced_refs: Dict[str, str],
    input_path_rel: str,
) -> List[str]:
    refs: List[str] = []
    for key in PHASE_INPUT_KEYS.get(phase_id, []):
        if key in produced_refs:
            refs.append(produced_refs[key])
            continue
        if key in request:
            raw = request[key]
            if isinstance(raw, str) and raw.strip():
                refs.append(raw.strip())
                continue
            if isinstance(raw, list):
                for item in raw:
                    text = str(item).strip()
                    if text:
                        refs.append(text)
                continue
    if not refs:
        return [input_path_rel]
    return refs


def synthesize_phase_outputs(
    *,
    root: Path,
    evidence_dir: Path,
    phase_id: str,
    actor: str,
    produced_refs: Dict[str, str],
) -> Dict[str, str]:
    phase_dir = evidence_dir / f"{phase_id}_outputs"
    phase_dir.mkdir(parents=True, exist_ok=True)

    output_refs: Dict[str, str] = {}
    fields = PHASE_OUTPUT_FIELDS.get(phase_id, [])
    for field in fields:
        artifact_path = phase_dir / f"{field}.json"
        dump_json(
            artifact_path,
            {
                "timestamp": now_iso(),
                "phase_id": phase_id,
                "actor": actor,
                "field": field,
                "mode": "collaboration-skeleton",
                "note": "本轮为协作骨架验证产物，后续可替换为真实子流程输出。",
            },
        )
        output_refs[field] = to_rel(artifact_path, root)
        produced_refs[field] = output_refs[field]
    return output_refs


def dispatch_phase(
    *,
    root: Path,
    evidence_dir: Path,
    phase: Dict[str, Any],
    input_refs: List[str],
    enabled: bool,
    dispatch_openclaw: bool,
    dispatch_instance_root: str,
    dispatch_openclaw_bin: str,
    dispatch_openclaw_stall_threshold_seconds: int,
    reset_openclaw_session: bool,
    strict_session_match: bool,
) -> Dict[str, Any]:
    phase_id = str(phase["phase_id"])
    actor = str(phase.get("actor") or "unknown")
    target_type = str(phase.get("target_type") or "")
    target_id = str(phase.get("target_id") or "")
    phase_name = str(phase.get("name") or phase_id)
    phase_purpose = str(phase.get("phase_purpose") or f"完成 {phase_name} 阶段目标")
    done_definition = str(phase.get("done_definition") or f"必须产出 {phase_name} 的可追溯输出引用")
    handoff_note = str(phase.get("handoff_note") or "将输出交接给下一阶段")
    input_ref = ",".join(input_refs)

    if not enabled:
        return {
            "enabled": False,
            "executed": False,
            "instance_id": "",
            "session_id": "",
            "actual_session_id": "",
            "dispatch_output_ref": "",
            "dispatch_context_ref": "",
            "dispatch_stdout_ref": "",
            "dispatch_stderr_ref": "",
        }

    dispatch_context_path = evidence_dir / f"{phase_id}_dispatch_context.md"
    dispatch_context_path.write_text(
        (
            f"# {phase_id} 协作上下文\n"
            f"- actor: {actor}\n"
            f"- target: {target_type}:{target_id}\n"
            f"- purpose: {phase_purpose}\n"
            f"- input_refs: {input_ref}\n"
            f"- done_definition: {done_definition}\n"
            f"- handoff_note: {handoff_note}\n"
        ),
        encoding="utf-8",
    )

    dispatch_message = (
        f"[{phase_id}] {phase_purpose}\n"
        f"target: {target_type}:{target_id}\n"
        f"输入上下文: {input_ref}\n"
        f"完成标准: {done_definition}\n"
        f"交接要求: {handoff_note}\n"
        "请输出阶段摘要与可追溯输出引用。"
    )

    dispatch_output_path = evidence_dir / f"{phase_id}_dispatch_output.json"
    cmd = [
        sys.executable,
        "skills/system/process-instance-manager/scripts/process_instance_runner.py",
        "start",
        "--process-id",
        "refactor",
        "--phase-id",
        phase_id,
        "--instance-root",
        str(resolve_path(root, dispatch_instance_root)),
        "--initiated-by",
        "bpm",
        "--input-ref",
        input_ref,
        "--dispatch-message",
        dispatch_message,
        "--openclaw-bin",
        dispatch_openclaw_bin,
        "--openclaw-stall-threshold-seconds",
        str(dispatch_openclaw_stall_threshold_seconds),
        "--output",
        to_rel(dispatch_output_path, root),
    ]
    if dispatch_openclaw:
        cmd.append("--execute-openclaw")
        if reset_openclaw_session:
            cmd.append("--reset-openclaw-session")
        if strict_session_match:
            cmd.append("--strict-session-match")

    proc = run_cmd(cmd, root)
    dispatch_stdout_path = evidence_dir / f"{phase_id}_dispatch_stdout.log"
    dispatch_stderr_path = evidence_dir / f"{phase_id}_dispatch_stderr.log"
    dispatch_stdout_path.write_text(proc.stdout, encoding="utf-8")
    dispatch_stderr_path.write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise RefactorError(
            f"{phase_id}_dispatch_failed:rc={proc.returncode}:stderr={proc.stderr.strip()}"
        )

    dispatch_output = load_json(dispatch_output_path)
    instance_id = str(dispatch_output.get("instance_id") or "")
    if not instance_id:
        raise RefactorError(f"{phase_id}_dispatch_missing_instance_id")

    session_id = ""
    binding_ref_raw = dispatch_output.get("session_binding_ref")
    if isinstance(binding_ref_raw, str) and binding_ref_raw.strip():
        binding_payload = load_json(resolve_path(root, binding_ref_raw))
        session_id = str(binding_payload.get("session_id") or "")
    if not session_id:
        raise RefactorError(f"{phase_id}_dispatch_missing_session_id")

    dispatch_exec = dispatch_output.get("dispatch")
    dispatch_executed = bool(dispatch_exec.get("executed")) if isinstance(dispatch_exec, dict) else False
    dispatch_rc = dispatch_exec.get("return_code") if isinstance(dispatch_exec, dict) else None
    actual_session_id = ""
    if isinstance(dispatch_exec, dict):
        actual_session_id = str(dispatch_exec.get("actual_session_id") or "").strip()

    if dispatch_openclaw:
        if not dispatch_executed:
            raise RefactorError(f"{phase_id}_dispatch_not_executed")
        if dispatch_rc != 0:
            raise RefactorError(f"{phase_id}_dispatch_nonzero_rc:{dispatch_rc}")
        if strict_session_match and actual_session_id and actual_session_id != session_id:
            raise RefactorError(
                f"{phase_id}_dispatch_session_mismatch:expected={session_id}:actual={actual_session_id}"
            )

    return {
        "enabled": True,
        "executed": dispatch_executed,
        "return_code": dispatch_rc,
        "instance_id": instance_id,
        "session_id": session_id,
        "actual_session_id": actual_session_id,
        "dispatch_output_ref": to_rel(dispatch_output_path, root),
        "dispatch_context_ref": to_rel(dispatch_context_path, root),
        "dispatch_stdout_ref": to_rel(dispatch_stdout_path, root),
        "dispatch_stderr_ref": to_rel(dispatch_stderr_path, root),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run refactor collaboration skeleton")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--evidence-dir",
        default="",
        help="Evidence directory path (repo-relative). Default runtime_data/execution/evidence/bpm-runtime/w3d_hotfix_refactor_cases/<run_id>/refactor/execution",
    )
    parser.add_argument("--run-id", default="", help="Optional run id")
    parser.add_argument("--enable-phase-dispatch", action="store_true", help="Enable phase dispatch")
    parser.set_defaults(dispatch_openclaw=True)
    parser.add_argument(
        "--dispatch-openclaw",
        dest="dispatch_openclaw",
        action="store_true",
        help="Enable real openclaw dispatch (default true)",
    )
    parser.add_argument(
        "--no-dispatch-openclaw",
        dest="dispatch_openclaw",
        action="store_false",
        help="Disable real openclaw dispatch",
    )
    parser.add_argument(
        "--dispatch-instance-root",
        default="tmp/m2-bpm-runtime/refactor/phase-dispatch/instances",
        help="Process instance root for phase dispatch",
    )
    parser.add_argument(
        "--dispatch-openclaw-bin",
        default="openclaw",
        help="OpenClaw binary used by phase dispatch",
    )
    parser.add_argument(
        "--dispatch-openclaw-stall-threshold-seconds",
        type=int,
        default=900,
        help=(
            "Per-phase stall threshold. Dispatch is considered stalled only when stdout/stderr "
            "and OpenClaw session signals remain unchanged for >= threshold (minimum 900s)."
        ),
    )
    parser.add_argument(
        "--dispatch-openclaw-timeout-seconds",
        dest="dispatch_openclaw_stall_threshold_seconds",
        type=int,
        help=argparse.SUPPRESS,
    )
    parser.set_defaults(reset_openclaw_session=True)
    parser.add_argument(
        "--reset-openclaw-session",
        dest="reset_openclaw_session",
        action="store_true",
        help="Reset openclaw session before each phase dispatch (default true)",
    )
    parser.add_argument(
        "--no-reset-openclaw-session",
        dest="reset_openclaw_session",
        action="store_false",
        help="Do not reset openclaw session before phase dispatch",
    )
    parser.set_defaults(strict_session_match=True)
    parser.add_argument(
        "--strict-session-match",
        dest="strict_session_match",
        action="store_true",
        help="Fail when actual openclaw session id mismatches context session id (default true)",
    )
    parser.add_argument(
        "--no-strict-session-match",
        dest="strict_session_match",
        action="store_false",
        help="Disable strict session match check",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    request = load_json(input_path)

    run_id = args.run_id.strip() or datetime.now(timezone.utc).strftime("refactor-%Y%m%dT%H%M%SZ")
    evidence_dir = resolve_path(
        root,
        args.evidence_dir.strip() or f"runtime_data/execution/evidence/bpm-runtime/w3d_hotfix_refactor_cases/{run_id}/refactor/execution",
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    runtime_trace_path = evidence_dir / "runtime_trace.json"
    fail_closed_path = evidence_dir / "fail_closed_record.json"
    phase_trace: List[Dict[str, Any]] = []
    produced_refs: Dict[str, str] = {}

    try:
        required = ["objective_context_ref", "tech_debt_ref", "target_asset_ref", "superpower_ref"]
        missing = [key for key in required if key not in request]
        if missing:
            raise RefactorError(f"missing required input fields: {','.join(missing)}")

        manifest = load_json(resolve_path(root, "processes/meta/refactor/process.json"))
        phases = manifest.get("phases")
        if not isinstance(phases, list) or not phases:
            raise RefactorError("refactor manifest phases empty")

        for phase in phases:
            if not isinstance(phase, dict):
                raise RefactorError("invalid phase definition")
            phase_id = str(phase.get("phase_id") or "")
            actor = str(phase.get("actor") or "unknown")
            if not phase_id:
                raise RefactorError("phase_id missing in manifest")

            input_refs = gather_phase_inputs(phase_id, request, produced_refs, to_rel(input_path, root))
            dispatch = dispatch_phase(
                root=root,
                evidence_dir=evidence_dir,
                phase=phase,
                input_refs=input_refs,
                enabled=args.enable_phase_dispatch,
                dispatch_openclaw=args.dispatch_openclaw,
                dispatch_instance_root=args.dispatch_instance_root,
                dispatch_openclaw_bin=args.dispatch_openclaw_bin,
                dispatch_openclaw_stall_threshold_seconds=args.dispatch_openclaw_stall_threshold_seconds,
                reset_openclaw_session=args.reset_openclaw_session,
                strict_session_match=args.strict_session_match,
            )
            phase_outputs = synthesize_phase_outputs(
                root=root,
                evidence_dir=evidence_dir,
                phase_id=phase_id,
                actor=actor,
                produced_refs=produced_refs,
            )
            phase_output_path = evidence_dir / f"{phase_id}_phase_output.json"
            dump_json(
                phase_output_path,
                {
                    "timestamp": now_iso(),
                    "phase_id": phase_id,
                    "actor": actor,
                    "inputs": input_refs,
                    "outputs": phase_outputs,
                    "collaboration_mode": "phase-isolated-session",
                },
            )
            phase_trace.append(
                {
                    "phase": phase_id,
                    "status": "pass",
                    "input_refs": input_refs,
                    "output_ref": to_rel(phase_output_path, root),
                    "dispatch": dispatch,
                    "ts": now_iso(),
                }
            )

        required_outputs = [
            "final_gate_verdict_ref",
            "lifecycle_transition_ref",
            "registry_sync_ref",
        ]
        missing_outputs = [key for key in required_outputs if key not in produced_refs]
        if missing_outputs:
            raise RefactorError(f"missing produced outputs: {','.join(missing_outputs)}")

        dump_json(
            runtime_trace_path,
            {
                "timestamp": now_iso(),
                "process_id": "refactor",
                "status": "ok",
                "input_ref": to_rel(input_path, root),
                "phase_trace": phase_trace,
                "collaboration_mode": "phase-isolated-session" if args.enable_phase_dispatch else "local-only",
                "dispatch_openclaw": args.dispatch_openclaw,
                "reset_openclaw_session": args.reset_openclaw_session,
                "strict_session_match": args.strict_session_match,
            },
        )
        domain_event_ref = emit_domain_event(
            root=root,
            process_id="refactor",
            event_name="m3.implementation.completed",
            severity="info",
            evidence_ref=to_rel(runtime_trace_path, root),
            owner_agent_id="bpm",
            asset_ref="process:refactor",
        )

        output = {
            "status": "ok",
            "process_id": "refactor",
            "collaboration_mode": "phase-isolated-session" if args.enable_phase_dispatch else "local-only",
            "phase_dispatch_enabled": args.enable_phase_dispatch,
            "dispatch_openclaw": args.dispatch_openclaw,
            "reset_openclaw_session": args.reset_openclaw_session,
            "strict_session_match": args.strict_session_match,
            "runtime_trace_ref": to_rel(runtime_trace_path, root),
            "evidence_ref": to_rel(evidence_dir, root),
            "domain_event_ref": domain_event_ref,
            "objective_ref": produced_refs.get("objective_ref", ""),
            "scope_baseline_ref": produced_refs.get("scope_baseline_ref", ""),
            "spec_ref": produced_refs.get("spec_ref", ""),
            "test_plan_ref": produced_refs.get("test_plan_ref", ""),
            "preparation_bundle_ref": produced_refs.get("preparation_bundle_ref", ""),
            "implementation_ref": produced_refs.get("implementation_ref", ""),
            "candidate_artifacts_ref": produced_refs.get("candidate_artifacts_ref", ""),
            "final_gate_verdict_ref": produced_refs.get("final_gate_verdict_ref", ""),
            "lifecycle_transition_ref": produced_refs.get("lifecycle_transition_ref", ""),
            "registry_sync_ref": produced_refs.get("registry_sync_ref", ""),
            "reasons": [
                "refactor_collaboration_skeleton_executed",
                f"phase_count={len(phase_trace)}",
            ],
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 0
    except Exception as exc:
        reason = str(exc)
        dump_json(
            fail_closed_path,
            {
                "timestamp": now_iso(),
                "status": "failed",
                "reason": reason,
                "fail_closed": True,
            },
        )
        dump_json(
            runtime_trace_path,
            {
                "timestamp": now_iso(),
                "process_id": "refactor",
                "status": "failed",
                "phase_trace": phase_trace,
                "reason": reason,
                "fail_closed_record_ref": to_rel(fail_closed_path, root),
            },
        )
        dump_json(
            output_path,
            {
                "status": "failed",
                "process_id": "refactor",
                "runtime_trace_ref": to_rel(runtime_trace_path, root),
                "evidence_ref": to_rel(evidence_dir, root),
                "fail_closed_record_ref": to_rel(fail_closed_path, root),
                "reasons": [reason],
            },
        )
        try:
            domain_event_ref = emit_domain_event(
                root=root,
                process_id="refactor",
                event_name="m3.implementation.failed",
                severity="critical",
                evidence_ref=to_rel(runtime_trace_path, root),
                owner_agent_id="bpm",
                asset_ref="process:refactor",
            )
            failed_output = load_json(output_path)
            failed_output["domain_event_ref"] = domain_event_ref
            dump_json(output_path, failed_output)
        except Exception:
            pass
        print(to_rel(output_path, root))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
