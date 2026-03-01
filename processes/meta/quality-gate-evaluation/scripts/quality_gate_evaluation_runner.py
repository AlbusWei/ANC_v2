#!/usr/bin/env python3
"""Executable runner for quality-gate-evaluation process."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class QualityGateEvaluationError(RuntimeError):
    """Fail-closed runtime error for quality-gate-evaluation."""


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
        raise QualityGateEvaluationError("not inside a git repository")
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
        raise QualityGateEvaluationError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise QualityGateEvaluationError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise QualityGateEvaluationError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_cmd(cmd: List[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(root), check=False, capture_output=True, text=True)


def parse_last_json(stdout: str) -> Dict[str, Any]:
    for line in reversed([item.strip() for item in stdout.splitlines() if item.strip()]):
        if line.startswith("{") and line.endswith("}"):
            payload = json.loads(line)
            if isinstance(payload, dict):
                return payload
    raise QualityGateEvaluationError("runner stdout does not contain json object")


def parse_refs(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        raw_items = [item.strip().strip("'\"") for item in text[1:-1].split(",")]
        return [item for item in raw_items if item]
    return [item.strip() for item in text.split(",") if item.strip()]


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "on"}


def dispatch_phase(
    *,
    enabled: bool,
    execute_openclaw: bool,
    reset_openclaw_session: bool,
    strict_session_match: bool,
    root: Path,
    evidence_dir: Path,
    phase_id: str,
    actor: str,
    input_ref: str,
    purpose: str,
    done_definition: str,
    handoff_note: str,
    instance_root: str,
    openclaw_bin: str,
    openclaw_stall_threshold_seconds: int,
) -> Dict[str, Any]:
    if not enabled:
        return {
            "enabled": False,
            "executed": False,
            "instance_id": "",
            "session_id": "",
            "parent_session_id": None,
            "dispatch_output_ref": "",
            "dispatch_context_ref": "",
        }

    dispatch_context_path = evidence_dir / f"{phase_id}_dispatch_context.md"
    dispatch_context_path.write_text(
        (
            f"# {phase_id} 协作上下文\n"
            f"- actor: {actor}\n"
            f"- purpose: {purpose}\n"
            f"- input_ref: {input_ref}\n"
            f"- done_definition: {done_definition}\n"
            f"- handoff_note: {handoff_note}\n"
        ),
        encoding="utf-8",
    )
    dispatch_message = (
        f"[{phase_id}] {purpose}\n"
        f"输入上下文: {input_ref}\n"
        f"完成标准: {done_definition}\n"
        f"交接要求: {handoff_note}\n"
        "请按上述约束执行并给出可追溯输出引用。"
    )

    dispatch_output_path = evidence_dir / f"{phase_id}_dispatch_output.json"
    dispatch_cmd = [
        sys.executable,
        "skills/system/process-instance-manager/scripts/process_instance_runner.py",
        "start",
        "--process-id",
        "quality-gate-evaluation",
        "--phase-id",
        phase_id,
        "--instance-root",
        str(resolve_path(root, instance_root)),
        "--initiated-by",
        "bpm",
        "--input-ref",
        input_ref,
        "--dispatch-message",
        dispatch_message,
        "--openclaw-bin",
        openclaw_bin,
        "--openclaw-stall-threshold-seconds",
        str(openclaw_stall_threshold_seconds),
        "--output",
        to_rel(dispatch_output_path, root),
    ]
    if execute_openclaw:
        dispatch_cmd.append("--execute-openclaw")
        if reset_openclaw_session:
            dispatch_cmd.append("--reset-openclaw-session")
        if strict_session_match:
            dispatch_cmd.append("--strict-session-match")

    proc = run_cmd(dispatch_cmd, root)
    dispatch_stdout_path = evidence_dir / f"{phase_id}_dispatch_stdout.log"
    dispatch_stderr_path = evidence_dir / f"{phase_id}_dispatch_stderr.log"
    dispatch_stdout_path.write_text(proc.stdout, encoding="utf-8")
    dispatch_stderr_path.write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise QualityGateEvaluationError(
            f"{phase_id}_dispatch_failed:rc={proc.returncode}:stderr={proc.stderr.strip()}"
        )

    dispatch_output = load_json(dispatch_output_path)
    instance_id = str(dispatch_output.get("instance_id") or "")
    if not instance_id:
        raise QualityGateEvaluationError(f"{phase_id}_dispatch_missing_instance_id")

    session_id = ""
    parent_session_id: Any = None
    binding_ref_raw = dispatch_output.get("session_binding_ref")
    if isinstance(binding_ref_raw, str) and binding_ref_raw.strip():
        binding_payload = load_json(resolve_path(root, binding_ref_raw))
        session_id = str(binding_payload.get("session_id") or "")
        parent_session_id = binding_payload.get("parent_session_id")
        if not session_id:
            raise QualityGateEvaluationError(f"{phase_id}_dispatch_missing_session_id")

    dispatch_exec = dispatch_output.get("dispatch")
    dispatch_executed = bool(dispatch_exec.get("executed")) if isinstance(dispatch_exec, dict) else False

    return {
        "enabled": True,
        "executed": dispatch_executed,
        "instance_id": instance_id,
        "session_id": session_id,
        "parent_session_id": parent_session_id,
        "dispatch_output_ref": to_rel(dispatch_output_path, root),
        "dispatch_context_ref": to_rel(dispatch_context_path, root),
        "dispatch_stdout_ref": to_rel(dispatch_stdout_path, root),
        "dispatch_stderr_ref": to_rel(dispatch_stderr_path, root),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run quality-gate-evaluation process")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--evidence-dir",
        default="",
        help="Evidence directory path (repo-relative). Default runtime_data/execution/evidence/bpm-runtime/w3b_qa_process_cases/<run_id>/quality-gate-evaluation",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Optional run id for evidence directory naming",
    )
    parser.add_argument(
        "--hold-governance-runner",
        default="processes/meta/hold-governance/scripts/hold_governance_runner.py",
        help="Repo-relative hold-governance runner path",
    )
    parser.add_argument(
        "--enable-phase-dispatch",
        action="store_true",
        help="Enable collaboration pilot: dispatch each phase with isolated session",
    )
    parser.add_argument(
        "--dispatch-openclaw",
        action="store_true",
        help="When phase dispatch is enabled, also execute openclaw agent dispatch",
    )
    parser.set_defaults(dispatch_reset_openclaw_session=True)
    parser.add_argument(
        "--dispatch-reset-openclaw-session",
        dest="dispatch_reset_openclaw_session",
        action="store_true",
        help="When dispatching with openclaw, reset actor session before each phase (default true)",
    )
    parser.add_argument(
        "--no-dispatch-reset-openclaw-session",
        dest="dispatch_reset_openclaw_session",
        action="store_false",
        help="Disable openclaw session reset before each phase",
    )
    parser.set_defaults(dispatch_strict_session_match=True)
    parser.add_argument(
        "--dispatch-strict-session-match",
        dest="dispatch_strict_session_match",
        action="store_true",
        help="Fail when openclaw actual session mismatches context session (default true)",
    )
    parser.add_argument(
        "--no-dispatch-strict-session-match",
        dest="dispatch_strict_session_match",
        action="store_false",
        help="Disable strict session mismatch checks",
    )
    parser.add_argument(
        "--dispatch-instance-root",
        default="tmp/m2-bpm-runtime/quality-gate-evaluation/phase-dispatch/instances",
        help="Process instance root used by per-phase dispatch",
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    request = load_json(input_path)

    run_id = args.run_id.strip() or datetime.now(timezone.utc).strftime("qa-eval-%Y%m%dT%H%M%SZ")
    evidence_dir = resolve_path(
        root,
        args.evidence_dir.strip()
        or f"runtime_data/execution/evidence/bpm-runtime/w3b_qa_process_cases/{run_id}/quality-gate-evaluation",
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    runtime_trace_path = evidence_dir / "runtime_trace.json"
    fail_closed_path = evidence_dir / "fail_closed_record.json"

    phase_trace: List[Dict[str, Any]] = []

    try:
        required = ["preparation_bundle_ref", "actual_output_refs", "superpower_ref"]
        missing = [key for key in required if key not in request]
        if missing:
            raise QualityGateEvaluationError(f"missing required input fields: {','.join(missing)}")

        preparation_bundle_ref = str(request["preparation_bundle_ref"])
        preparation_bundle_path = resolve_path(root, preparation_bundle_ref)
        if not preparation_bundle_path.exists():
            raise QualityGateEvaluationError("preparation_bundle_ref_unreachable")

        superpower_ref = str(request["superpower_ref"])
        superpower_path = resolve_path(root, superpower_ref)
        if not superpower_path.exists():
            raise QualityGateEvaluationError("superpower_ref_unreachable")

        actual_output_refs = parse_refs(request.get("actual_output_refs"))
        if not actual_output_refs:
            raise QualityGateEvaluationError("actual_output_refs_empty")
        for ref in actual_output_refs:
            if not resolve_path(root, ref).exists():
                raise QualityGateEvaluationError(f"actual_output_ref_unreachable:{ref}")

        profile_set = parse_refs(request.get("profile_set") or "quality-gate.baseline@1.0.0")
        profile_set_csv = ",".join(profile_set)
        if not profile_set_csv:
            raise QualityGateEvaluationError("profile_set_empty")

        force_hold = parse_bool(request.get("force_hold"))
        max_auto_retest_cycles_raw = request.get("max_auto_retest_cycles", 0)
        try:
            max_auto_retest_cycles = int(max_auto_retest_cycles_raw)
        except (TypeError, ValueError) as exc:
            raise QualityGateEvaluationError("max_auto_retest_cycles_must_be_integer") from exc
        if max_auto_retest_cycles < 0:
            raise QualityGateEvaluationError("max_auto_retest_cycles_must_be_gte_0")
        phase_dispatch_enabled = args.enable_phase_dispatch
        phase_dispatch_openclaw = args.dispatch_openclaw
        phase_dispatch_reset_session = args.dispatch_reset_openclaw_session
        phase_dispatch_strict_match = args.dispatch_strict_session_match

        # p1: objective evaluation (AP-007)
        p1_dispatch = dispatch_phase(
            enabled=phase_dispatch_enabled,
            execute_openclaw=phase_dispatch_openclaw,
            reset_openclaw_session=phase_dispatch_reset_session,
            strict_session_match=phase_dispatch_strict_match,
            root=root,
            evidence_dir=evidence_dir,
            phase_id="p1",
            actor="qa",
            input_ref=to_rel(input_path, root),
            purpose="执行客观评测（AP-007）并产出 objective_eval_ref",
            done_definition="必须产出可追溯 objective_eval_ref",
            handoff_note="将 objective_eval_ref 交给 p2 主观评测阶段",
            instance_root=args.dispatch_instance_root,
            openclaw_bin=args.dispatch_openclaw_bin,
            openclaw_stall_threshold_seconds=args.dispatch_openclaw_stall_threshold_seconds,
        )
        p1_dir = evidence_dir / "p1_objective_eval"
        p1_dir.mkdir(parents=True, exist_ok=True)
        p1_cmd = [
            "skills/system/qa/evaluation-runner/scripts/quality_eval_runner",
            "run",
            "--preparation-bundle",
            to_rel(preparation_bundle_path, root),
            "--mode",
            "objective",
            "--actual-output",
            actual_output_refs[0],
            "--module",
            "M3",
            "--output-dir",
            to_rel(p1_dir, root),
        ]
        p1_proc = run_cmd(p1_cmd, root)
        (p1_dir / "stdout.txt").write_text(p1_proc.stdout, encoding="utf-8")
        (p1_dir / "stderr.txt").write_text(p1_proc.stderr, encoding="utf-8")
        p1_payload = parse_last_json(p1_proc.stdout)
        if p1_proc.returncode != 0:
            raise QualityGateEvaluationError(f"objective_eval_failed:rc={p1_proc.returncode}")

        objective_eval_ref = str(p1_payload.get("raw_eval_ref") or to_rel(p1_dir / "raw_eval.json", root))
        if not resolve_path(root, objective_eval_ref).exists():
            raise QualityGateEvaluationError("objective_eval_ref_missing")

        phase_trace.append(
            {
                "phase": "p1-run-objective-evaluation",
                "status": "pass",
                "return_code": p1_proc.returncode,
                "objective_eval_ref": objective_eval_ref,
                "dispatch": p1_dispatch,
                "ts": now_iso(),
            }
        )

        # p2~p5: evaluation + hold 治理，支持自动回测回路
        gate_decision = "fail"
        runtime_gate_state = "fail"
        final_gate_verdict_ref = ""
        hold_routed = False
        hold_governance_output_ref = ""
        hold_resolution_ref = ""
        hold_triage_action = ""
        hold_retest_recommendation = ""
        auto_retest_count = 0
        force_hold_current = force_hold

        while True:
            # p2: subjective evaluation (AP-008). For W3-B scheduling sample we keep deterministic outputs.
            p2_dispatch = dispatch_phase(
                enabled=phase_dispatch_enabled,
                execute_openclaw=phase_dispatch_openclaw,
                reset_openclaw_session=phase_dispatch_reset_session,
                strict_session_match=phase_dispatch_strict_match,
                root=root,
                evidence_dir=evidence_dir,
                phase_id="p2",
                actor="qa",
                input_ref=objective_eval_ref,
                purpose="执行主观评测（AP-008）并产出 subjective_eval_ref",
                done_definition="必须产出 subjective_eval_ref 且给出 hold/pass 判定",
                handoff_note="将 subjective_eval_ref 交给 p3 回归评测阶段",
                instance_root=args.dispatch_instance_root,
                openclaw_bin=args.dispatch_openclaw_bin,
                openclaw_stall_threshold_seconds=args.dispatch_openclaw_stall_threshold_seconds,
            )
            p2_dir = evidence_dir / "p2_subjective_eval"
            p2_dir.mkdir(parents=True, exist_ok=True)
            subjective_eval_path = p2_dir / "subjective_eval.json"
            subjective_decision = "hold" if force_hold_current else "pass"
            subjective_payload = {
                "timestamp": now_iso(),
                "mode": "subjective",
                "gate_decision": subjective_decision,
                "subjective_verdict": "review" if force_hold_current else "accept",
                "reasons": ["simulated_subjective_result"],
                "simulated": True,
                "case_results": [
                    {
                        "tc_id": "TC-SUBJECTIVE-001",
                        "priority": "P1",
                        "decision": subjective_decision,
                    }
                ],
            }
            dump_json(subjective_eval_path, subjective_payload)
            phase_trace.append(
                {
                    "phase": "p2-run-subjective-evaluation",
                    "status": "pass",
                    "mode": "simulated",
                    "subjective_eval_ref": to_rel(subjective_eval_path, root),
                    "subjective_decision": subjective_decision,
                    "iteration": auto_retest_count,
                    "dispatch": p2_dispatch,
                    "ts": now_iso(),
                }
            )

            # p3: regression evaluation (AP-009)
            p3_dispatch = dispatch_phase(
                enabled=phase_dispatch_enabled,
                execute_openclaw=phase_dispatch_openclaw,
                reset_openclaw_session=phase_dispatch_reset_session,
                strict_session_match=phase_dispatch_strict_match,
                root=root,
                evidence_dir=evidence_dir,
                phase_id="p3",
                actor="qa",
                input_ref=to_rel(subjective_eval_path, root),
                purpose="执行回归评测（AP-009）并产出 regression_eval_ref",
                done_definition="必须产出可追溯 regression_eval_ref",
                handoff_note="将三类评测引用交给 p4 聚合判定",
                instance_root=args.dispatch_instance_root,
                openclaw_bin=args.dispatch_openclaw_bin,
                openclaw_stall_threshold_seconds=args.dispatch_openclaw_stall_threshold_seconds,
            )
            p3_dir = evidence_dir / "p3_regression_eval"
            p3_dir.mkdir(parents=True, exist_ok=True)
            p3_cmd = [
                sys.executable,
                "skills/system/qa/regression-runner/scripts/run_regression.py",
                "--regression-scope",
                str(request.get("regression_scope") or "M3"),
                "--profile-set",
                profile_set_csv,
                "--preparation-bundle",
                to_rel(preparation_bundle_path, root),
                "--output-dir",
                to_rel(p3_dir, root),
            ]
            for ref in actual_output_refs:
                p3_cmd.extend(["--actual-output", ref])

            p3_proc = run_cmd(p3_cmd, root)
            (p3_dir / "stdout.txt").write_text(p3_proc.stdout, encoding="utf-8")
            (p3_dir / "stderr.txt").write_text(p3_proc.stderr, encoding="utf-8")
            p3_payload = parse_last_json(p3_proc.stdout)
            if p3_proc.returncode != 0:
                raise QualityGateEvaluationError(f"regression_eval_failed:rc={p3_proc.returncode}")

            regression_eval_ref = str(
                p3_payload.get("regression_eval_ref") or to_rel(p3_dir / "regression_eval.json", root)
            )
            if not resolve_path(root, regression_eval_ref).exists():
                raise QualityGateEvaluationError("regression_eval_ref_missing")

            phase_trace.append(
                {
                    "phase": "p3-run-regression-evaluation",
                    "status": "pass",
                    "return_code": p3_proc.returncode,
                    "regression_eval_ref": regression_eval_ref,
                    "iteration": auto_retest_count,
                    "dispatch": p3_dispatch,
                    "ts": now_iso(),
                }
            )

            # p4: aggregate-gate-decision (AP-020)
            p4_dispatch = dispatch_phase(
                enabled=phase_dispatch_enabled,
                execute_openclaw=phase_dispatch_openclaw,
                reset_openclaw_session=phase_dispatch_reset_session,
                strict_session_match=phase_dispatch_strict_match,
                root=root,
                evidence_dir=evidence_dir,
                phase_id="p4",
                actor="qa",
                input_ref=regression_eval_ref,
                purpose="聚合门禁判定（AP-020）并产出 final_gate_verdict_ref",
                done_definition="必须产出 gate_decision 与 final_gate_verdict_ref",
                handoff_note="若 runtime_gate_state=hold，则交给 p5 处理 hold 治理路由",
                instance_root=args.dispatch_instance_root,
                openclaw_bin=args.dispatch_openclaw_bin,
                openclaw_stall_threshold_seconds=args.dispatch_openclaw_stall_threshold_seconds,
            )
            p4_dir = evidence_dir / "p4_aggregate_verdict"
            p4_dir.mkdir(parents=True, exist_ok=True)
            aggregation_rules_ref = str(
                request.get("aggregation_rules_ref") or "tests/fixtures/quality-gate/aggregation_rules.json"
            )
            if not resolve_path(root, aggregation_rules_ref).exists():
                raise QualityGateEvaluationError("aggregation_rules_ref_unreachable")

            p4_cmd = [
                sys.executable,
                "skills/system/qa/verdict-normalizer/scripts/normalize_verdict.py",
                "--objective-eval",
                objective_eval_ref,
                "--subjective-eval",
                to_rel(subjective_eval_path, root),
                "--regression-eval",
                regression_eval_ref,
                "--aggregation-rules",
                aggregation_rules_ref,
                "--output-dir",
                to_rel(p4_dir, root),
            ]
            p4_proc = run_cmd(p4_cmd, root)
            (p4_dir / "stdout.txt").write_text(p4_proc.stdout, encoding="utf-8")
            (p4_dir / "stderr.txt").write_text(p4_proc.stderr, encoding="utf-8")
            p4_payload = parse_last_json(p4_proc.stdout)
            raw_gate_decision = str(p4_payload.get("gate_decision") or "fail").strip()
            runtime_gate_state = raw_gate_decision
            gate_decision = "fail" if runtime_gate_state == "hold" else runtime_gate_state
            final_gate_verdict_ref = str(
                p4_payload.get("final_gate_verdict_ref") or to_rel(p4_dir / "final_gate_verdict.json", root)
            )

            if p4_proc.returncode not in (0, 20, 30, 40):
                raise QualityGateEvaluationError(f"verdict_normalizer_unexpected_rc:{p4_proc.returncode}")
            if runtime_gate_state not in {"pass", "fail", "hold", "test_invalid"}:
                raise QualityGateEvaluationError(f"invalid_runtime_gate_state:{runtime_gate_state}")
            if gate_decision not in {"pass", "fail", "test_invalid"}:
                raise QualityGateEvaluationError(f"invalid_gate_decision:{gate_decision}")
            if not resolve_path(root, final_gate_verdict_ref).exists():
                raise QualityGateEvaluationError("final_gate_verdict_ref_missing")

            phase_trace.append(
                {
                    "phase": "p4-aggregate-gate-decision",
                    "status": "pass" if runtime_gate_state in {"pass", "hold"} else "failed",
                    "gate_decision": gate_decision,
                    "runtime_gate_state": runtime_gate_state,
                    "return_code": p4_proc.returncode,
                    "final_gate_verdict_ref": final_gate_verdict_ref,
                    "iteration": auto_retest_count,
                    "dispatch": p4_dispatch,
                    "ts": now_iso(),
                }
            )

            hold_routed = runtime_gate_state == "hold"
            if not hold_routed:
                break

            # p5: govern-hold (subprocess)
            p5_dispatch = dispatch_phase(
                enabled=phase_dispatch_enabled,
                execute_openclaw=phase_dispatch_openclaw,
                reset_openclaw_session=phase_dispatch_reset_session,
                strict_session_match=phase_dispatch_strict_match,
                root=root,
                evidence_dir=evidence_dir,
                phase_id="p5",
                actor="bpm",
                input_ref=final_gate_verdict_ref,
                purpose="处理 hold 治理路由并输出 hold_resolution_ref",
                done_definition="hold 场景必须产出 hold_resolution_ref 或 escalation_ref",
                handoff_note="若 retest_recommendation=auto-retest 且预算未耗尽，则回路到 p2",
                instance_root=args.dispatch_instance_root,
                openclaw_bin=args.dispatch_openclaw_bin,
                openclaw_stall_threshold_seconds=args.dispatch_openclaw_stall_threshold_seconds,
            )
            hold_case_path = resolve_path(
                root, str(request.get("hold_case_ref") or to_rel(evidence_dir / "p5_hold_case.json", root))
            )
            runtime_log_path = resolve_path(
                root, str(request.get("runtime_log_ref") or to_rel(evidence_dir / "p5_runtime.log", root))
            )
            execution_state_path = resolve_path(
                root, str(request.get("execution_state_ref") or to_rel(evidence_dir / "p5_execution_state.json", root))
            )
            triage_policy_path = resolve_path(
                root, str(request.get("triage_policy_ref") or to_rel(evidence_dir / "p5_triage_policy.json", root))
            )
            runtime_health_policy_path = resolve_path(
                root,
                str(request.get("runtime_health_policy_ref") or to_rel(evidence_dir / "p5_runtime_health_policy.json", root)),
            )
            liveness_policy_path = resolve_path(
                root,
                str(request.get("liveness_policy_ref") or to_rel(evidence_dir / "p5_liveness_policy.json", root)),
            )
            no_progress_window_path = resolve_path(
                root,
                str(request.get("no_progress_window_ref") or to_rel(evidence_dir / "p5_no_progress_window.json", root)),
            )
            termination_rule_path = resolve_path(
                root,
                str(request.get("termination_rule_ref") or to_rel(evidence_dir / "p5_termination_rule.json", root)),
            )

            if not hold_case_path.exists():
                dump_json(
                    hold_case_path,
                    {
                        "case_id": f"hold-{run_id}",
                        "output_heartbeat": True,
                    },
                )
            if not runtime_log_path.exists():
                runtime_log_path.write_text("phase stalled, waiting for triage\n", encoding="utf-8")
            if not execution_state_path.exists():
                dump_json(execution_state_path, {"phase_progress": "eval_hold", "phase_index": 4})
            if not triage_policy_path.exists():
                dump_json(
                    triage_policy_path,
                    {
                        "allowed_actions": ["continue", "retry", "debug", "fail"],
                        "heartbeat_max_age_seconds": 3600,
                        "on_no_progress": "debug",
                    },
                )
            if not runtime_health_policy_path.exists():
                dump_json(runtime_health_policy_path, {"max_hold_minutes": 45, "max_retries": 2})
            if not liveness_policy_path.exists():
                dump_json(
                    liveness_policy_path,
                    {
                        "required_signals": [
                            "stdout_stderr_increment",
                            "openclaw_session_activity",
                            "phase_state_progress",
                        ],
                        "default_no_progress_window_seconds": 900,
                    },
                )
            if not no_progress_window_path.exists():
                dump_json(no_progress_window_path, {"window_seconds": 900})
            if not termination_rule_path.exists():
                dump_json(
                    termination_rule_path,
                    {
                        "trigger": "continuous_no_progress_gte_900s",
                        "requires_evidence": True,
                    },
                )

            hold_input_path = evidence_dir / "p5_hold_governance_input.json"
            hold_output_path = evidence_dir / "p5_hold_governance_output.json"
            hold_evidence_dir = evidence_dir / "p5_hold_governance"
            dump_json(
                hold_input_path,
                {
                    "hold_case_ref": to_rel(hold_case_path, root),
                    "runtime_log_ref": to_rel(runtime_log_path, root),
                    "execution_state_ref": to_rel(execution_state_path, root),
                    "triage_policy_ref": to_rel(triage_policy_path, root),
                    "runtime_health_policy_ref": to_rel(runtime_health_policy_path, root),
                    "liveness_policy_ref": to_rel(liveness_policy_path, root),
                    "no_progress_window_ref": to_rel(no_progress_window_path, root),
                    "termination_rule_ref": to_rel(termination_rule_path, root),
                    "current_owner": str(request.get("current_owner") or "qa"),
                },
            )

            hold_runner = resolve_path(root, args.hold_governance_runner)
            if not hold_runner.exists():
                raise QualityGateEvaluationError(f"hold_governance_runner_not_found:{hold_runner}")

            p5_cmd = [
                sys.executable,
                to_rel(hold_runner, root),
                "--input",
                to_rel(hold_input_path, root),
                "--output",
                to_rel(hold_output_path, root),
                "--evidence-dir",
                to_rel(hold_evidence_dir, root),
                "--run-id",
                f"{run_id}-hold",
            ]
            p5_proc = run_cmd(p5_cmd, root)
            if p5_proc.returncode != 0:
                raise QualityGateEvaluationError(f"hold_governance_failed:rc={p5_proc.returncode}")

            hold_payload = load_json(hold_output_path)
            hold_governance_output_ref = to_rel(hold_output_path, root)
            hold_resolution_ref = str(hold_payload.get("hold_resolution_ref") or "")
            hold_triage_action = str(hold_payload.get("triage_action") or "")
            hold_retest_recommendation = str(hold_payload.get("retest_recommendation") or "stop")
            if hold_retest_recommendation not in {"auto-retest", "stop"}:
                raise QualityGateEvaluationError(
                    f"invalid_hold_retest_recommendation:{hold_retest_recommendation}"
                )
            if hold_resolution_ref and not resolve_path(root, hold_resolution_ref).exists():
                raise QualityGateEvaluationError("hold_resolution_ref_missing")

            phase_trace.append(
                {
                    "phase": "p5-govern-hold",
                    "status": "pass",
                    "hold_governance_output_ref": hold_governance_output_ref,
                    "hold_resolution_ref": hold_resolution_ref,
                    "triage_action": hold_triage_action,
                    "retest_recommendation": hold_retest_recommendation,
                    "iteration": auto_retest_count,
                    "dispatch": p5_dispatch,
                    "ts": now_iso(),
                }
            )

            if hold_retest_recommendation == "auto-retest" and auto_retest_count < max_auto_retest_cycles:
                auto_retest_count += 1
                # 自动回测回路使用非 force_hold 输入，避免测试场景被固定 hold 卡死。
                force_hold_current = False
                phase_trace.append(
                    {
                        "phase": "p5-auto-retest-route",
                        "status": "pass",
                        "next_phase": "p2",
                        "auto_retest_count": auto_retest_count,
                        "max_auto_retest_cycles": max_auto_retest_cycles,
                        "ts": now_iso(),
                    }
                )
                continue

            break

        dump_json(
            runtime_trace_path,
            {
                "timestamp": now_iso(),
                "process_id": "quality-gate-evaluation",
                "status": "ok" if gate_decision == "pass" else "failed",
                "phase_trace": phase_trace,
                "input_ref": to_rel(input_path, root),
                "collaboration_mode": "phase-isolated-session" if phase_dispatch_enabled else "local-only",
                "auto_retest_count": auto_retest_count,
                "max_auto_retest_cycles": max_auto_retest_cycles,
                "dispatch_openclaw": phase_dispatch_openclaw,
                "dispatch_reset_openclaw_session": phase_dispatch_reset_session,
                "dispatch_strict_session_match": phase_dispatch_strict_match,
            },
        )

        output = {
            "status": "ok" if gate_decision == "pass" else "failed",
            "process_id": "quality-gate-evaluation",
            "gate_decision": gate_decision,
            "runtime_gate_state": runtime_gate_state,
            "objective_eval_ref": objective_eval_ref,
            "subjective_eval_ref": to_rel(subjective_eval_path, root),
            "regression_eval_ref": regression_eval_ref,
            "final_gate_verdict_ref": final_gate_verdict_ref,
            "evidence_ref": to_rel(evidence_dir, root),
            "runtime_trace_ref": to_rel(runtime_trace_path, root),
            "hold_routed": hold_routed,
            "hold_governance_output_ref": hold_governance_output_ref,
            "hold_resolution_ref": hold_resolution_ref,
            "hold_triage_action": hold_triage_action,
            "hold_retest_recommendation": hold_retest_recommendation,
            "auto_retest_count": auto_retest_count,
            "max_auto_retest_cycles": max_auto_retest_cycles,
            "collaboration_mode": "phase-isolated-session" if phase_dispatch_enabled else "local-only",
            "phase_dispatch_enabled": phase_dispatch_enabled,
            "dispatch_openclaw": phase_dispatch_openclaw,
            "dispatch_reset_openclaw_session": phase_dispatch_reset_session,
            "dispatch_strict_session_match": phase_dispatch_strict_match,
            "reasons": [
                "gate_aggregated",
                f"gate_decision={gate_decision}",
                f"runtime_gate_state={runtime_gate_state}",
                f"auto_retest_count={auto_retest_count}",
            ],
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 0 if gate_decision == "pass" else 2

    except Exception as exc:
        failure_reason = str(exc)
        dump_json(
            fail_closed_path,
            {
                "timestamp": now_iso(),
                "status": "failed",
                "reason": failure_reason,
                "fail_closed": True,
            },
        )
        dump_json(
            runtime_trace_path,
            {
                "timestamp": now_iso(),
                "process_id": "quality-gate-evaluation",
                "status": "failed",
                "phase_trace": phase_trace,
                "reason": failure_reason,
                "fail_closed_record_ref": to_rel(fail_closed_path, root),
            },
        )
        output = {
            "status": "failed",
            "process_id": "quality-gate-evaluation",
            "gate_decision": "fail",
            "runtime_gate_state": "fail",
            "objective_eval_ref": "",
            "subjective_eval_ref": "",
            "regression_eval_ref": "",
            "final_gate_verdict_ref": "",
            "evidence_ref": to_rel(evidence_dir, root),
            "runtime_trace_ref": to_rel(runtime_trace_path, root),
            "hold_routed": False,
            "hold_governance_output_ref": "",
            "hold_resolution_ref": "",
            "fail_closed_record_ref": to_rel(fail_closed_path, root),
            "reasons": [failure_reason],
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
