#!/usr/bin/env python3
"""Thread-3 M1 runtime closure regression runner.

目标：
1. 复用现有流程 runner，覆盖 pass / fail-closed / hold 三类判定。
2. 产出可追溯证据包，供 Thread-4 直接复测与状态联动。
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


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
        raise RuntimeError("not inside git repository")
    return Path(proc.stdout.strip()).resolve()


def resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def parse_profile_set(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_command_logs(case_dir: Path, commands: List[Dict[str, Any]]) -> None:
    command_log_path = case_dir / "commands.txt"
    lines: List[str] = []
    for item in commands:
        lines.append(f"[{item['step']}] rc={item['return_code']}")
        lines.append(f"cmd: {item['command']}")
        lines.append(f"stdout: {item['stdout_ref']}")
        lines.append(f"stderr: {item['stderr_ref']}")
        lines.append("")
    command_log_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    dump_json(case_dir / "command_trace.json", {"commands": commands, "ts": now_iso()})


def exec_step(
    *,
    root: Path,
    case_dir: Path,
    step: str,
    cmd: List[str],
    commands: List[Dict[str, Any]],
) -> subprocess.CompletedProcess[str]:
    proc = run_cmd(cmd, root)
    stdout_path = case_dir / f"{step}.stdout.txt"
    stderr_path = case_dir / f"{step}.stderr.txt"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    commands.append(
        {
            "step": step,
            "command": " ".join(cmd),
            "return_code": proc.returncode,
            "stdout_ref": to_rel(stdout_path, root),
            "stderr_ref": to_rel(stderr_path, root),
        }
    )
    return proc


def path_exists_for_ref(root: Path, ref: str) -> bool:
    if not ref:
        return False
    return resolve_path(root, ref).exists()


def finalize_case(
    *,
    root: Path,
    case_dir: Path,
    case_id: str,
    status: str,
    gate_decision: str,
    decision_class: str,
    commands: List[Dict[str, Any]],
    inputs: List[Path],
    outputs: List[Path],
    logs: List[Path],
    critical_refs: Dict[str, str],
    notes: List[str],
) -> Dict[str, Any]:
    write_command_logs(case_dir, commands)
    logs_full = logs + [case_dir / "commands.txt", case_dir / "command_trace.json"]
    evidence_index_path = case_dir / "evidence_index.json"
    dump_json(
        evidence_index_path,
        {
            "tc_id": case_id,
            "status": status,
            "gate_decision": gate_decision,
            "decision_class": decision_class,
            "inputs": [to_rel(path, root) for path in inputs],
            "outputs": [to_rel(path, root) for path in outputs],
            "logs": [to_rel(path, root) for path in logs_full],
            "critical_refs": critical_refs,
            "notes": notes,
            "generated_at": now_iso(),
        },
    )
    return {
        "id": case_id,
        "status": status,
        "gate_decision": gate_decision,
        "decision_class": decision_class,
        "evidence_index_ref": to_rel(evidence_index_path, root),
        "critical_refs": critical_refs,
        "notes": notes,
    }


def run_tc_001(
    *,
    root: Path,
    evidence_root: Path,
    prep_runner: Path,
    eval_runner: Path,
    lifecycle_runner: Path,
    test_doc_ref: str,
    actual_output_ref: str,
    profile_set: str,
) -> Dict[str, Any]:
    case_id = "TC-M1-CHAIN-001"
    case_dir = evidence_root / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    commands: List[Dict[str, Any]] = []
    inputs: List[Path] = []
    outputs: List[Path] = []
    logs: List[Path] = []
    notes: List[str] = []

    prep_input = case_dir / "prep_input.json"
    prep_output = case_dir / "prep_output.json"
    eval_input = case_dir / "eval_input.json"
    eval_output = case_dir / "eval_output.json"
    lifecycle_input = case_dir / "lifecycle_input.json"
    lifecycle_output = case_dir / "lifecycle_output.json"
    target_asset_ref = case_dir / "target_asset_snapshot.json"

    dump_json(
        prep_input,
        {
            "objective_ref": "obj-m3-full-development-loop",
            "spec_ref": "docs/design/processes/full-development-process.md",
            "test_doc_ref": test_doc_ref,
            "risk_focus": ["P0", "P1"],
        },
    )
    dump_json(
        target_asset_ref,
        {
            "asset_id": "process:full-development",
            "asset_type": "process",
            "status": "review",
            "lifecycle_status": "review",
            "owner": "bpm",
            "source": "tc-m1-chain-001",
        },
    )
    inputs.extend([prep_input, target_asset_ref])

    prep_cmd = [
        sys.executable,
        to_rel(prep_runner, root),
        "--input",
        to_rel(prep_input, root),
        "--output",
        to_rel(prep_output, root),
        "--evidence-dir",
        to_rel(case_dir / "preparation", root),
        "--run-id",
        "TC-M1-CHAIN-001-prep",
        "--profile-set",
        profile_set,
    ]
    prep_proc = exec_step(root=root, case_dir=case_dir, step="prep", cmd=prep_cmd, commands=commands)
    logs.extend([case_dir / "prep.stdout.txt", case_dir / "prep.stderr.txt"])

    if prep_proc.returncode != 0 or not prep_output.exists():
        notes.append("preparation 未通过，主链路中断。")
        return finalize_case(
            root=root,
            case_dir=case_dir,
            case_id=case_id,
            status="fail",
            gate_decision="unknown",
            decision_class="pass",
            commands=commands,
            inputs=inputs,
            outputs=[prep_output],
            logs=logs,
            critical_refs={},
            notes=notes,
        )

    prep_payload = load_json(prep_output)
    preparation_bundle_ref = str(prep_payload.get("preparation_bundle_ref") or "")
    preparation_verdict = str(prep_payload.get("verdict") or "")
    if preparation_verdict != "pass" or not preparation_bundle_ref:
        notes.append("preparation 输出不满足 pass 条件。")
        return finalize_case(
            root=root,
            case_dir=case_dir,
            case_id=case_id,
            status="fail",
            gate_decision=preparation_verdict or "unknown",
            decision_class="pass",
            commands=commands,
            inputs=inputs,
            outputs=[prep_output],
            logs=logs,
            critical_refs={"prep_output_ref": to_rel(prep_output, root)},
            notes=notes,
        )

    dump_json(
        eval_input,
        {
            "preparation_bundle_ref": preparation_bundle_ref,
            "actual_output_refs": [actual_output_ref],
            "profile_set": parse_profile_set(profile_set),
            "force_hold": False,
        },
    )
    inputs.append(eval_input)

    eval_cmd = [
        sys.executable,
        to_rel(eval_runner, root),
        "--input",
        to_rel(eval_input, root),
        "--output",
        to_rel(eval_output, root),
        "--evidence-dir",
        to_rel(case_dir / "evaluation", root),
        "--run-id",
        "TC-M1-CHAIN-001-eval",
    ]
    eval_proc = exec_step(root=root, case_dir=case_dir, step="eval", cmd=eval_cmd, commands=commands)
    logs.extend([case_dir / "eval.stdout.txt", case_dir / "eval.stderr.txt"])

    if eval_proc.returncode != 0 or not eval_output.exists():
        notes.append("evaluation 未通过，无法进入 lifecycle-review。")
        return finalize_case(
            root=root,
            case_dir=case_dir,
            case_id=case_id,
            status="fail",
            gate_decision="fail",
            decision_class="pass",
            commands=commands,
            inputs=inputs,
            outputs=[prep_output, eval_output],
            logs=logs,
            critical_refs={
                "prep_output_ref": to_rel(prep_output, root),
                "eval_output_ref": to_rel(eval_output, root),
            },
            notes=notes,
        )

    eval_payload = load_json(eval_output)
    gate_decision = str(eval_payload.get("gate_decision") or "")
    final_gate_verdict_ref = str(eval_payload.get("final_gate_verdict_ref") or "")
    if gate_decision != "pass" or not path_exists_for_ref(root, final_gate_verdict_ref):
        notes.append("evaluation 输出未形成可用 pass verdict。")
        return finalize_case(
            root=root,
            case_dir=case_dir,
            case_id=case_id,
            status="fail",
            gate_decision=gate_decision or "unknown",
            decision_class="pass",
            commands=commands,
            inputs=inputs,
            outputs=[prep_output, eval_output],
            logs=logs,
            critical_refs={
                "prep_output_ref": to_rel(prep_output, root),
                "eval_output_ref": to_rel(eval_output, root),
                "final_gate_verdict_ref": final_gate_verdict_ref,
            },
            notes=notes,
        )

    dump_json(
        lifecycle_input,
        {
            "final_gate_verdict_ref": final_gate_verdict_ref,
            "target_asset_ref": to_rel(target_asset_ref, root),
            "requested_transition": {
                "from_status": "review",
                "to_status": "active",
            },
        },
    )
    inputs.append(lifecycle_input)

    lifecycle_cmd = [
        sys.executable,
        to_rel(lifecycle_runner, root),
        "--input",
        to_rel(lifecycle_input, root),
        "--output",
        to_rel(lifecycle_output, root),
        "--evidence-dir",
        to_rel(case_dir / "lifecycle", root),
        "--run-id",
        "TC-M1-CHAIN-001-lifecycle",
    ]
    lifecycle_proc = exec_step(root=root, case_dir=case_dir, step="lifecycle", cmd=lifecycle_cmd, commands=commands)
    logs.extend([case_dir / "lifecycle.stdout.txt", case_dir / "lifecycle.stderr.txt"])
    outputs.extend([prep_output, eval_output, lifecycle_output])

    if lifecycle_proc.returncode != 0 or not lifecycle_output.exists():
        notes.append("lifecycle-review 执行失败。")
        return finalize_case(
            root=root,
            case_dir=case_dir,
            case_id=case_id,
            status="fail",
            gate_decision=gate_decision,
            decision_class="pass",
            commands=commands,
            inputs=inputs,
            outputs=outputs,
            logs=logs,
            critical_refs={
                "final_gate_verdict_ref": final_gate_verdict_ref,
                "lifecycle_output_ref": to_rel(lifecycle_output, root),
            },
            notes=notes,
        )

    lifecycle_payload = load_json(lifecycle_output)
    lifecycle_transition_ref = str(lifecycle_payload.get("lifecycle_transition_ref") or "")
    registry_sync_ref = str(lifecycle_payload.get("registry_sync_ref") or "")
    lifecycle_review_report_ref = str(lifecycle_payload.get("lifecycle_review_report_ref") or "")
    ok = (
        lifecycle_payload.get("status") == "succeeded"
        and path_exists_for_ref(root, lifecycle_transition_ref)
        and path_exists_for_ref(root, registry_sync_ref)
        and path_exists_for_ref(root, lifecycle_review_report_ref)
    )
    if not ok:
        notes.append("lifecycle-review 输出缺失关键引用。")

    return finalize_case(
        root=root,
        case_dir=case_dir,
        case_id=case_id,
        status="pass" if ok else "fail",
        gate_decision=gate_decision,
        decision_class="pass",
        commands=commands,
        inputs=inputs,
        outputs=outputs,
        logs=logs,
        critical_refs={
            "prep_output_ref": to_rel(prep_output, root),
            "eval_output_ref": to_rel(eval_output, root),
            "final_gate_verdict_ref": final_gate_verdict_ref,
            "lifecycle_output_ref": to_rel(lifecycle_output, root),
            "lifecycle_transition_ref": lifecycle_transition_ref,
            "registry_sync_ref": registry_sync_ref,
            "lifecycle_review_report_ref": lifecycle_review_report_ref,
        },
        notes=notes or ["M3->M1->M4 pass 主链路已闭环。"],
    )


def run_tc_002(
    *,
    root: Path,
    evidence_root: Path,
    prep_runner: Path,
    lifecycle_runner: Path,
) -> Dict[str, Any]:
    case_id = "TC-M1-CHAIN-002"
    case_dir = evidence_root / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    commands: List[Dict[str, Any]] = []
    inputs: List[Path] = []
    outputs: List[Path] = []
    logs: List[Path] = []
    notes: List[str] = []

    prep_input = case_dir / "prep_input_missing_required.json"
    prep_output = case_dir / "prep_output.json"
    lifecycle_input = case_dir / "lifecycle_input.json"
    lifecycle_output = case_dir / "lifecycle_output.json"
    target_asset_ref = case_dir / "target_asset_snapshot.json"

    # 刻意缺失 risk_focus，触发 quality-gate-preparation 的 test_invalid。
    dump_json(
        prep_input,
        {
            "objective_ref": "obj-m1-unified-quality-gate",
            "spec_ref": "docs/design/modules/M1-openjudge-adapter-spec.md",
            "test_doc_ref": "docs/design/modules/evidence/quality-gate/runtime-validation-round-2/fixtures/TEST_rule.md",
        },
    )
    dump_json(
        target_asset_ref,
        {
            "asset_id": "process:hotfix",
            "status": "review",
            "lifecycle_status": "review",
        },
    )
    inputs.extend([prep_input, target_asset_ref])

    prep_cmd = [
        sys.executable,
        to_rel(prep_runner, root),
        "--input",
        to_rel(prep_input, root),
        "--output",
        to_rel(prep_output, root),
        "--evidence-dir",
        to_rel(case_dir / "preparation", root),
        "--run-id",
        "TC-M1-CHAIN-002-prep",
    ]
    prep_proc = exec_step(root=root, case_dir=case_dir, step="prep", cmd=prep_cmd, commands=commands)
    logs.extend([case_dir / "prep.stdout.txt", case_dir / "prep.stderr.txt"])
    outputs.append(prep_output)

    prep_verdict = "unknown"
    prep_fail_closed_ref = ""
    if prep_output.exists():
        prep_payload = load_json(prep_output)
        prep_verdict = str(prep_payload.get("verdict") or "unknown")
        prep_fail_closed_ref = str(prep_payload.get("fail_closed_record_ref") or "")

    # 在门禁证据缺失时，lifecycle-review 必须 Fail-Closed 且不得产出 transition。
    missing_final_gate_ref = to_rel(case_dir / "missing_final_gate_verdict.json", root)
    dump_json(
        lifecycle_input,
        {
            "final_gate_verdict_ref": missing_final_gate_ref,
            "target_asset_ref": to_rel(target_asset_ref, root),
            "requested_transition": {
                "from_status": "review",
                "to_status": "active",
            },
        },
    )
    inputs.append(lifecycle_input)

    lifecycle_cmd = [
        sys.executable,
        to_rel(lifecycle_runner, root),
        "--input",
        to_rel(lifecycle_input, root),
        "--output",
        to_rel(lifecycle_output, root),
        "--evidence-dir",
        to_rel(case_dir / "lifecycle", root),
        "--run-id",
        "TC-M1-CHAIN-002-lifecycle",
    ]
    lifecycle_proc = exec_step(root=root, case_dir=case_dir, step="lifecycle", cmd=lifecycle_cmd, commands=commands)
    logs.extend([case_dir / "lifecycle.stdout.txt", case_dir / "lifecycle.stderr.txt"])
    outputs.append(lifecycle_output)

    lifecycle_transition_ref = ""
    lifecycle_fail_closed_ref = ""
    lifecycle_status = "unknown"
    if lifecycle_output.exists():
        lifecycle_payload = load_json(lifecycle_output)
        lifecycle_transition_ref = str(lifecycle_payload.get("lifecycle_transition_ref") or "")
        lifecycle_fail_closed_ref = str(lifecycle_payload.get("fail_closed_record_ref") or "")
        lifecycle_status = str(lifecycle_payload.get("status") or "unknown")

    ok = (
        prep_proc.returncode != 0
        and prep_verdict in {"test_invalid", "fail", "failed"}
        and lifecycle_proc.returncode != 0
        and lifecycle_status == "failed"
        and lifecycle_transition_ref == ""
        and path_exists_for_ref(root, lifecycle_fail_closed_ref)
    )
    if not ok:
        notes.append("未满足 fail/test_invalid + lifecycle transition 阻断条件。")

    return finalize_case(
        root=root,
        case_dir=case_dir,
        case_id=case_id,
        status="pass" if ok else "fail",
        gate_decision=prep_verdict,
        decision_class="fail_closed",
        commands=commands,
        inputs=inputs,
        outputs=outputs,
        logs=logs,
        critical_refs={
            "prep_output_ref": to_rel(prep_output, root),
            "prep_fail_closed_ref": prep_fail_closed_ref,
            "lifecycle_output_ref": to_rel(lifecycle_output, root),
            "lifecycle_fail_closed_ref": lifecycle_fail_closed_ref,
            "lifecycle_transition_ref": lifecycle_transition_ref,
        },
        notes=notes or ["关键输入缺失触发 test_invalid/fail-closed，且 lifecycle transition 已阻断。"],
    )


def run_tc_003(
    *,
    root: Path,
    evidence_root: Path,
    prep_runner: Path,
    eval_runner: Path,
    test_doc_ref: str,
    actual_output_ref: str,
    profile_set: str,
    hold_case_ref: str,
    execution_state_ref: str,
    triage_policy_ref: str,
) -> Dict[str, Any]:
    case_id = "TC-M1-CHAIN-003"
    case_dir = evidence_root / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    commands: List[Dict[str, Any]] = []
    inputs: List[Path] = []
    outputs: List[Path] = []
    logs: List[Path] = []
    notes: List[str] = []

    prep_input = case_dir / "prep_input.json"
    prep_output = case_dir / "prep_output.json"
    eval_input = case_dir / "eval_input_hold.json"
    eval_output = case_dir / "eval_output.json"
    runtime_log_ref = case_dir / "hold_runtime.log"
    runtime_health_policy_ref = case_dir / "runtime_health_policy.json"

    dump_json(
        prep_input,
        {
            "objective_ref": "obj-m1-unified-quality-gate",
            "spec_ref": "docs/design/modules/M1-openjudge-adapter-spec.md",
            "test_doc_ref": test_doc_ref,
            "risk_focus": ["P0", "P1"],
        },
    )
    runtime_log_ref.write_text("subjective_check_pending\n", encoding="utf-8")
    dump_json(runtime_health_policy_ref, {"max_hold_minutes": 45, "max_retries": 2})
    inputs.extend([prep_input, runtime_log_ref, runtime_health_policy_ref])

    prep_cmd = [
        sys.executable,
        to_rel(prep_runner, root),
        "--input",
        to_rel(prep_input, root),
        "--output",
        to_rel(prep_output, root),
        "--evidence-dir",
        to_rel(case_dir / "preparation", root),
        "--run-id",
        "TC-M1-CHAIN-003-prep",
        "--profile-set",
        profile_set,
    ]
    prep_proc = exec_step(root=root, case_dir=case_dir, step="prep", cmd=prep_cmd, commands=commands)
    logs.extend([case_dir / "prep.stdout.txt", case_dir / "prep.stderr.txt"])
    outputs.append(prep_output)

    if prep_proc.returncode != 0 or not prep_output.exists():
        notes.append("preparation 未通过，无法进入 hold 路由验证。")
        return finalize_case(
            root=root,
            case_dir=case_dir,
            case_id=case_id,
            status="fail",
            gate_decision="unknown",
            decision_class="hold",
            commands=commands,
            inputs=inputs,
            outputs=outputs,
            logs=logs,
            critical_refs={},
            notes=notes,
        )

    prep_payload = load_json(prep_output)
    preparation_bundle_ref = str(prep_payload.get("preparation_bundle_ref") or "")
    if str(prep_payload.get("verdict") or "") != "pass" or not preparation_bundle_ref:
        notes.append("preparation 未产出可用 bundle。")
        return finalize_case(
            root=root,
            case_dir=case_dir,
            case_id=case_id,
            status="fail",
            gate_decision=str(prep_payload.get("verdict") or "unknown"),
            decision_class="hold",
            commands=commands,
            inputs=inputs,
            outputs=outputs,
            logs=logs,
            critical_refs={"prep_output_ref": to_rel(prep_output, root)},
            notes=notes,
        )

    dump_json(
        eval_input,
        {
            "preparation_bundle_ref": preparation_bundle_ref,
            "actual_output_refs": [actual_output_ref],
            "profile_set": parse_profile_set(profile_set),
            "force_hold": True,
            "hold_case_ref": hold_case_ref,
            "runtime_log_ref": to_rel(runtime_log_ref, root),
            "execution_state_ref": execution_state_ref,
            "triage_policy_ref": triage_policy_ref,
            "runtime_health_policy_ref": to_rel(runtime_health_policy_ref, root),
            "current_owner": "qa",
        },
    )
    inputs.append(eval_input)

    eval_cmd = [
        sys.executable,
        to_rel(eval_runner, root),
        "--input",
        to_rel(eval_input, root),
        "--output",
        to_rel(eval_output, root),
        "--evidence-dir",
        to_rel(case_dir / "evaluation", root),
        "--run-id",
        "TC-M1-CHAIN-003-eval",
    ]
    eval_proc = exec_step(root=root, case_dir=case_dir, step="eval", cmd=eval_cmd, commands=commands)
    logs.extend([case_dir / "eval.stdout.txt", case_dir / "eval.stderr.txt"])
    outputs.append(eval_output)

    if eval_proc.returncode != 0 or not eval_output.exists():
        notes.append("evaluation 未形成 hold 结果。")
        return finalize_case(
            root=root,
            case_dir=case_dir,
            case_id=case_id,
            status="fail",
            gate_decision="fail",
            decision_class="hold",
            commands=commands,
            inputs=inputs,
            outputs=outputs,
            logs=logs,
            critical_refs={"eval_output_ref": to_rel(eval_output, root)},
            notes=notes,
        )

    eval_payload = load_json(eval_output)
    gate_decision = str(eval_payload.get("gate_decision") or "")
    hold_routed = bool(eval_payload.get("hold_routed"))
    hold_governance_output_ref = str(eval_payload.get("hold_governance_output_ref") or "")
    hold_resolution_ref = str(eval_payload.get("hold_resolution_ref") or "")
    ok = (
        gate_decision == "hold"
        and hold_routed
        and path_exists_for_ref(root, hold_governance_output_ref)
        and path_exists_for_ref(root, hold_resolution_ref)
    )
    if not ok:
        notes.append("hold 路由或 hold_resolution 证据缺失。")

    return finalize_case(
        root=root,
        case_dir=case_dir,
        case_id=case_id,
        status="pass" if ok else "fail",
        gate_decision=gate_decision,
        decision_class="hold",
        commands=commands,
        inputs=inputs,
        outputs=outputs,
        logs=logs,
        critical_refs={
            "prep_output_ref": to_rel(prep_output, root),
            "eval_output_ref": to_rel(eval_output, root),
            "hold_governance_output_ref": hold_governance_output_ref,
            "hold_resolution_ref": hold_resolution_ref,
        },
        notes=notes or ["evaluation hold 已成功路由 hold-governance 并产出 hold_resolution_ref。"],
    )


def run_tc_004(
    *,
    root: Path,
    evidence_root: Path,
    prep_runner: Path,
    eval_runner: Path,
    test_doc_ref: str,
    actual_output_ref: str,
    profile_set: str,
) -> Dict[str, Any]:
    case_id = "TC-M1-CHAIN-004"
    case_dir = evidence_root / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    commands: List[Dict[str, Any]] = []
    inputs: List[Path] = []
    outputs: List[Path] = []
    logs: List[Path] = []
    notes: List[str] = []

    m5_request_input = case_dir / "m5_request.json"
    prep_input = case_dir / "prep_input.json"
    prep_output = case_dir / "prep_output.json"
    eval_input = case_dir / "eval_input.json"
    eval_output = case_dir / "eval_output.json"

    dump_json(
        m5_request_input,
        {
            "proposal_id": "m5-min-entry-001",
            "source_module": "M5",
            "target_gate_module": "M1",
            "goal": "验证 M5 调用 M1 门禁入口可执行",
            "requested_by": "analyst",
        },
    )
    dump_json(
        prep_input,
        {
            "objective_ref": "obj-m5-self-evolution-min-entry",
            "spec_ref": "docs/design/modules/M5-self-evolution.md",
            "test_doc_ref": test_doc_ref,
            "risk_focus": ["P0", "P1"],
            "m5_request_ref": to_rel(m5_request_input, root),
        },
    )
    inputs.extend([m5_request_input, prep_input])

    prep_cmd = [
        sys.executable,
        to_rel(prep_runner, root),
        "--input",
        to_rel(prep_input, root),
        "--output",
        to_rel(prep_output, root),
        "--evidence-dir",
        to_rel(case_dir / "preparation", root),
        "--run-id",
        "TC-M1-CHAIN-004-prep",
        "--profile-set",
        profile_set,
    ]
    prep_proc = exec_step(root=root, case_dir=case_dir, step="prep", cmd=prep_cmd, commands=commands)
    logs.extend([case_dir / "prep.stdout.txt", case_dir / "prep.stderr.txt"])
    outputs.append(prep_output)

    if prep_proc.returncode != 0 or not prep_output.exists():
        notes.append("M5 -> M1 接入在 preparation 阶段失败。")
        return finalize_case(
            root=root,
            case_dir=case_dir,
            case_id=case_id,
            status="fail",
            gate_decision="unknown",
            decision_class="pass",
            commands=commands,
            inputs=inputs,
            outputs=outputs,
            logs=logs,
            critical_refs={"m5_request_ref": to_rel(m5_request_input, root)},
            notes=notes,
        )

    prep_payload = load_json(prep_output)
    preparation_bundle_ref = str(prep_payload.get("preparation_bundle_ref") or "")
    if str(prep_payload.get("verdict") or "") != "pass" or not preparation_bundle_ref:
        notes.append("M5 -> M1 接入未产出可用 preparation bundle。")
        return finalize_case(
            root=root,
            case_dir=case_dir,
            case_id=case_id,
            status="fail",
            gate_decision=str(prep_payload.get("verdict") or "unknown"),
            decision_class="pass",
            commands=commands,
            inputs=inputs,
            outputs=outputs,
            logs=logs,
            critical_refs={
                "m5_request_ref": to_rel(m5_request_input, root),
                "prep_output_ref": to_rel(prep_output, root),
            },
            notes=notes,
        )

    dump_json(
        eval_input,
        {
            "preparation_bundle_ref": preparation_bundle_ref,
            "actual_output_refs": [actual_output_ref],
            "profile_set": parse_profile_set(profile_set),
            "force_hold": False,
            "source_module": "M5",
        },
    )
    inputs.append(eval_input)

    eval_cmd = [
        sys.executable,
        to_rel(eval_runner, root),
        "--input",
        to_rel(eval_input, root),
        "--output",
        to_rel(eval_output, root),
        "--evidence-dir",
        to_rel(case_dir / "evaluation", root),
        "--run-id",
        "TC-M1-CHAIN-004-eval",
    ]
    eval_proc = exec_step(root=root, case_dir=case_dir, step="eval", cmd=eval_cmd, commands=commands)
    logs.extend([case_dir / "eval.stdout.txt", case_dir / "eval.stderr.txt"])
    outputs.append(eval_output)

    if eval_proc.returncode != 0 or not eval_output.exists():
        notes.append("M5 -> M1 接入在 evaluation 阶段失败。")
        return finalize_case(
            root=root,
            case_dir=case_dir,
            case_id=case_id,
            status="fail",
            gate_decision="fail",
            decision_class="pass",
            commands=commands,
            inputs=inputs,
            outputs=outputs,
            logs=logs,
            critical_refs={
                "m5_request_ref": to_rel(m5_request_input, root),
                "prep_output_ref": to_rel(prep_output, root),
                "eval_output_ref": to_rel(eval_output, root),
            },
            notes=notes,
        )

    eval_payload = load_json(eval_output)
    gate_decision = str(eval_payload.get("gate_decision") or "")
    final_gate_verdict_ref = str(eval_payload.get("final_gate_verdict_ref") or "")
    ok = gate_decision == "pass" and path_exists_for_ref(root, final_gate_verdict_ref)
    if not ok:
        notes.append("M5 -> M1 接入未产出可用 pass verdict。")

    return finalize_case(
        root=root,
        case_dir=case_dir,
        case_id=case_id,
        status="pass" if ok else "fail",
        gate_decision=gate_decision,
        decision_class="pass",
        commands=commands,
        inputs=inputs,
        outputs=outputs,
        logs=logs,
        critical_refs={
            "m5_request_ref": to_rel(m5_request_input, root),
            "prep_output_ref": to_rel(prep_output, root),
            "eval_output_ref": to_rel(eval_output, root),
            "final_gate_verdict_ref": final_gate_verdict_ref,
        },
        notes=notes or ["M5 已最小接入 M1 门禁入口（preparation + evaluation 可执行）。"],
    )


def build_markdown_summary(summary: Dict[str, Any]) -> str:
    coverage = summary["decision_coverage"]
    lines: List[str] = [
        "# Runtime Validation Round 6 Summary",
        "",
        f"- 生成时间: `{summary['ts']}`",
        f"- 总体结果: `{summary['status']}`",
        f"- 用例总数: `{summary['total']}`",
        f"- 通过数: `{summary['passed']}`",
        f"- 失败数: `{summary['failed']}`",
        "",
        "## 判定覆盖",
        "",
        f"- pass: `{coverage.get('pass', False)}`",
        f"- fail_closed: `{coverage.get('fail_closed', False)}`",
        f"- hold: `{coverage.get('hold', False)}`",
        "",
        "## 用例结论",
        "",
    ]
    for case in summary["cases"]:
        lines.extend(
            [
                f"### {case['id']}",
                f"- status: `{case['status']}`",
                f"- gate_decision: `{case['gate_decision']}`",
                f"- decision_class: `{case['decision_class']}`",
                f"- evidence_index_ref: `{case['evidence_index_ref']}`",
            ]
        )
        refs = case.get("critical_refs", {})
        if refs:
            lines.append("- critical_refs:")
            for key, value in refs.items():
                lines.append(f"  - `{key}`: `{value}`")
        notes = case.get("notes", [])
        if notes:
            lines.append("- notes:")
            for note in notes:
                lines.append(f"  - {note}")
        lines.append("")

    lines.extend(
        [
            "## Thread-4 联动引用",
            "",
        ]
    )
    for key, payload in summary.get("thread4_refs", {}).items():
        lines.append(f"### {key}")
        for sub_key, ref in payload.items():
            lines.append(f"- `{sub_key}`: `{ref}`")
        lines.append("")

    lines.extend(
        [
            "## 自然语言结论",
            "",
            summary.get("natural_language_conclusion", ""),
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run M1 runtime closure regression (Thread-3)")
    parser.add_argument(
        "--preparation-runner",
        default="processes/meta/quality-gate-preparation/scripts/quality_gate_preparation_runner.py",
        help="Repo-relative preparation runner path",
    )
    parser.add_argument(
        "--evaluation-runner",
        default="processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py",
        help="Repo-relative evaluation runner path",
    )
    parser.add_argument(
        "--lifecycle-review-runner",
        default="processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py",
        help="Repo-relative lifecycle review runner path",
    )
    parser.add_argument(
        "--test-doc-ref",
        default="docs/design/modules/evidence/quality-gate/runtime-validation-round-2/fixtures/TEST_rule.md",
        help="Repo-relative TEST doc fixture",
    )
    parser.add_argument(
        "--actual-output-ref",
        default="docs/design/modules/evidence/quality-gate/runtime-validation-round-2/fixtures/actual_output_pass.txt",
        help="Repo-relative actual output fixture",
    )
    parser.add_argument(
        "--hold-case-ref",
        default="docs/design/modules/evidence/quality-gate/runtime-validation-round-2/fixtures/hold_case.json",
        help="Repo-relative hold case fixture",
    )
    parser.add_argument(
        "--execution-state-ref",
        default="docs/design/modules/evidence/quality-gate/runtime-validation-round-2/fixtures/execution_state.json",
        help="Repo-relative execution state fixture",
    )
    parser.add_argument(
        "--triage-policy-ref",
        default="docs/design/modules/evidence/quality-gate/runtime-validation-round-2/fixtures/triage_policy.json",
        help="Repo-relative triage policy fixture",
    )
    parser.add_argument(
        "--profile-set",
        default="quality-gate.baseline@1.0.0",
        help="Comma-separated profile ids",
    )
    parser.add_argument(
        "--evidence-root",
        default="docs/design/modules/evidence/quality-gate/runtime-validation-round-6-m1-closure",
        help="Repo-relative evidence root directory",
    )
    parser.add_argument(
        "--report",
        default="docs/design/modules/evidence/quality-gate/runtime-validation-round-6-m1-closure/runtime_summary.json",
        help="Repo-relative summary json output path",
    )
    parser.add_argument(
        "--markdown-report",
        default="docs/design/modules/evidence/quality-gate/runtime-validation-round-6-m1-closure/runtime_summary.md",
        help="Repo-relative summary markdown output path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    prep_runner = resolve_path(root, args.preparation_runner)
    eval_runner = resolve_path(root, args.evaluation_runner)
    lifecycle_runner = resolve_path(root, args.lifecycle_review_runner)
    test_doc_path = resolve_path(root, args.test_doc_ref)
    actual_output_path = resolve_path(root, args.actual_output_ref)
    hold_case_path = resolve_path(root, args.hold_case_ref)
    execution_state_path = resolve_path(root, args.execution_state_ref)
    triage_policy_path = resolve_path(root, args.triage_policy_ref)
    evidence_root = resolve_path(root, args.evidence_root)
    report_path = resolve_path(root, args.report)
    markdown_report_path = resolve_path(root, args.markdown_report)

    required_paths = [
        prep_runner,
        eval_runner,
        lifecycle_runner,
        test_doc_path,
        actual_output_path,
        hold_case_path,
        execution_state_path,
        triage_policy_path,
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise RuntimeError(f"missing required paths: {missing}")

    profile_items = parse_profile_set(args.profile_set)
    if not profile_items:
        raise RuntimeError("profile_set cannot be empty")

    if evidence_root.exists():
        shutil.rmtree(evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=True)

    cases: List[Dict[str, Any]] = []
    cases.append(
        run_tc_001(
            root=root,
            evidence_root=evidence_root,
            prep_runner=prep_runner,
            eval_runner=eval_runner,
            lifecycle_runner=lifecycle_runner,
            test_doc_ref=to_rel(test_doc_path, root),
            actual_output_ref=to_rel(actual_output_path, root),
            profile_set=args.profile_set,
        )
    )
    cases.append(
        run_tc_002(
            root=root,
            evidence_root=evidence_root,
            prep_runner=prep_runner,
            lifecycle_runner=lifecycle_runner,
        )
    )
    cases.append(
        run_tc_003(
            root=root,
            evidence_root=evidence_root,
            prep_runner=prep_runner,
            eval_runner=eval_runner,
            test_doc_ref=to_rel(test_doc_path, root),
            actual_output_ref=to_rel(actual_output_path, root),
            profile_set=args.profile_set,
            hold_case_ref=to_rel(hold_case_path, root),
            execution_state_ref=to_rel(execution_state_path, root),
            triage_policy_ref=to_rel(triage_policy_path, root),
        )
    )
    cases.append(
        run_tc_004(
            root=root,
            evidence_root=evidence_root,
            prep_runner=prep_runner,
            eval_runner=eval_runner,
            test_doc_ref=to_rel(test_doc_path, root),
            actual_output_ref=to_rel(actual_output_path, root),
            profile_set=args.profile_set,
        )
    )

    total = len(cases)
    failed_cases = [case for case in cases if case["status"] != "pass"]
    passed = total - len(failed_cases)
    decision_coverage = {"pass": False, "fail_closed": False, "hold": False}
    for case in cases:
        if case["status"] == "pass" and case["decision_class"] in decision_coverage:
            decision_coverage[case["decision_class"]] = True

    missing_coverage = [key for key, value in decision_coverage.items() if not value]
    status = "pass" if (not failed_cases and not missing_coverage) else "fail"

    thread4_refs = {
        "tc_m1_chain_001_pass": {
            "evidence_index_ref": cases[0]["evidence_index_ref"],
            "final_gate_verdict_ref": cases[0]["critical_refs"].get("final_gate_verdict_ref", ""),
            "lifecycle_transition_ref": cases[0]["critical_refs"].get("lifecycle_transition_ref", ""),
            "registry_sync_ref": cases[0]["critical_refs"].get("registry_sync_ref", ""),
        },
        "tc_m1_chain_002_fail_closed": {
            "evidence_index_ref": cases[1]["evidence_index_ref"],
            "prep_output_ref": cases[1]["critical_refs"].get("prep_output_ref", ""),
            "lifecycle_fail_closed_ref": cases[1]["critical_refs"].get("lifecycle_fail_closed_ref", ""),
            "lifecycle_output_ref": cases[1]["critical_refs"].get("lifecycle_output_ref", ""),
        },
        "tc_m1_chain_003_hold": {
            "evidence_index_ref": cases[2]["evidence_index_ref"],
            "eval_output_ref": cases[2]["critical_refs"].get("eval_output_ref", ""),
            "hold_governance_output_ref": cases[2]["critical_refs"].get("hold_governance_output_ref", ""),
            "hold_resolution_ref": cases[2]["critical_refs"].get("hold_resolution_ref", ""),
        },
        "tc_m1_chain_004_m5_entry": {
            "evidence_index_ref": cases[3]["evidence_index_ref"],
            "m5_request_ref": cases[3]["critical_refs"].get("m5_request_ref", ""),
            "eval_output_ref": cases[3]["critical_refs"].get("eval_output_ref", ""),
            "final_gate_verdict_ref": cases[3]["critical_refs"].get("final_gate_verdict_ref", ""),
        },
    }

    summary = {
        "ts": now_iso(),
        "suite": "TC-M1-CHAIN-001~004",
        "status": status,
        "total": total,
        "passed": passed,
        "failed": len(failed_cases),
        "failed_case_ids": [case["id"] for case in failed_cases],
        "missing_decision_coverage": missing_coverage,
        "decision_coverage": decision_coverage,
        "evidence_root": to_rel(evidence_root, root),
        "cases": cases,
        "thread4_refs": thread4_refs,
        "natural_language_conclusion": (
            "本轮已覆盖 pass、fail-closed 与 hold 三类判定证据，并验证 M5 最小接入 M1 门禁入口可执行。"
            if status == "pass"
            else "本轮未满足 Thread-3 收口门禁，请先修复失败用例或判定覆盖缺口。"
        ),
    }
    dump_json(report_path, summary)

    markdown_report = build_markdown_summary(summary)
    markdown_report_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_report_path.write_text(markdown_report, encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
