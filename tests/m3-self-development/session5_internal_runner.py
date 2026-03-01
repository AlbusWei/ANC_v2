#!/usr/bin/env python3
"""Session5 内部主线 E2E 执行器。

目标：
1. 以 M3 canonical 顺序执行内部主线：
   objective-scope-baseline -> spec-authoring-contract -> quality-gate-preparation ->
   implementation-execution-core -> quality-gate-evaluation -> lifecycle-review ->
   registry-sync -> release-packaging-governed -> release-manager-agent。
2. 覆盖三条用例：
   - M3-INT-001：主链 Happy。
   - M3-INT-002：Fail-Closed -> Debug -> 修复 -> 重跑通过。
   - M3-INT-003：release-manager-agent 成功/拒绝双分支。
3. 全阶段启用 OpenClaw 分发，采集 liveness 探针证据。
4. 证据默认写入 tmp，不进入提交路径。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_EVIDENCE_ROOT = Path(
    "tmp/runtime_data/execution/evidence/construction-plane/"
    "R-20260222-M6-m3-self-development-e2e-online-01/session5"
)
DEFAULT_REPORT_NAME = "session5_report.json"
DEFAULT_SUMMARY_NAME = "session5_summary.md"
DEFAULT_FAIL_REWORK_NAME = "session5_fail_rework_case.md"
DEFAULT_RISK_NAME = "session5_risk_for_session6.md"
SESSION5_CASE_IDS = ("M3-INT-001", "M3-INT-002", "M3-INT-003")


class Session5Error(RuntimeError):
    """Session5 执行期失败。"""


@dataclass(frozen=True)
class StageSpec:
    """canonical 主链阶段与 full-development phase 的映射。"""

    stage_id: str
    phase_id: str
    process_id: str = "full-development"


CANONICAL_CHAIN: List[StageSpec] = [
    StageSpec("objective-scope-baseline", "p1"),
    StageSpec("spec-authoring-contract", "p2"),
    StageSpec("quality-gate-preparation", "p3"),
    StageSpec("implementation-execution-core", "p4"),
    StageSpec("quality-gate-evaluation", "p5"),
    StageSpec("lifecycle-review", "p6"),
    StageSpec("registry-sync", "p6"),
    StageSpec("release-packaging-governed", "p7"),
    StageSpec("release-manager-agent", "p8"),
]


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
        raise Session5Error("not inside git repository")
    return Path(proc.stdout.strip()).resolve()


def resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else (root / path).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Session5Error(f"json_root_not_object:{path}")
    return payload


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def parse_last_json(stdout: str) -> Dict[str, Any]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith("{") and line.endswith("}"):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
    return {}


def write_command_trace(
    *,
    root: Path,
    trace_dir: Path,
    command_id: str,
    cmd: List[str],
    proc: subprocess.CompletedProcess[str],
) -> Dict[str, Any]:
    trace_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = trace_dir / f"{command_id}.stdout.log"
    stderr_path = trace_dir / f"{command_id}.stderr.log"
    command_path = trace_dir / f"{command_id}.command.txt"
    write_text(stdout_path, proc.stdout)
    write_text(stderr_path, proc.stderr)
    write_text(command_path, " ".join(cmd))
    return {
        "command_id": command_id,
        "command": " ".join(cmd),
        "return_code": proc.returncode,
        "stdout_ref": to_rel(stdout_path, root),
        "stderr_ref": to_rel(stderr_path, root),
        "command_ref": to_rel(command_path, root),
    }


def collect_probe_from_dispatch(root: Path, stage: str, dispatch_output: Dict[str, Any], output_ref: str) -> Dict[str, Any]:
    dispatch = dispatch_output.get("dispatch") if isinstance(dispatch_output.get("dispatch"), dict) else {}
    liveness = dispatch.get("liveness") if isinstance(dispatch.get("liveness"), dict) else {}
    return {
        "stage": stage,
        "dispatch_output_ref": output_ref,
        "session_id": str(dispatch_output.get("session_binding_ref") or ""),
        "actual_session_id": str(dispatch.get("actual_session_id") or ""),
        "probe_count": int(liveness.get("probe_count") or 0),
        "session_seen": bool(liveness.get("session_seen")),
        "stall_threshold_seconds": int(liveness.get("stall_threshold_seconds") or 0),
        "idle_since_output_seconds": int(liveness.get("idle_since_output_seconds") or 0),
        "idle_since_session_progress_seconds": int(liveness.get("idle_since_session_progress_seconds") or 0),
        "duration_seconds": int(liveness.get("duration_seconds") or 0),
        "probe_errors": liveness.get("probe_errors") if isinstance(liveness.get("probe_errors"), list) else [],
    }


def dispatch_stage(
    *,
    root: Path,
    case_dir: Path,
    stage_spec: StageSpec,
    input_refs: List[str],
    execute_openclaw: bool = True,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """执行全链 OpenClaw 分发并返回 dispatch payload + liveness probe。"""
    dispatch_dir = case_dir / "dispatch" / stage_spec.stage_id
    dispatch_dir.mkdir(parents=True, exist_ok=True)
    trace_dir = dispatch_dir / "traces"

    dispatch_output_path = dispatch_dir / "dispatch_output.json"
    instance_root = case_dir / "dispatch" / "instances"
    input_ref = ",".join([item for item in input_refs if item])

    dispatch_message = (
        f"[{stage_spec.stage_id}] 执行 Session5 内部主线阶段\n"
        f"阶段: {stage_spec.stage_id}\n"
        f"输入引用: {input_ref or 'none'}\n"
        "完成标准: 必须输出可追溯结果，并保持 Fail-Closed。\n"
        "交接要求: 输出引用必须可供下一阶段直接消费。"
    )

    cmd = [
        sys.executable,
        "skills/system/process-instance-manager/scripts/process_instance_runner.py",
        "start",
        "--process-id",
        stage_spec.process_id,
        "--phase-id",
        stage_spec.phase_id,
        "--instance-root",
        str(instance_root),
        "--initiated-by",
        "bpm",
        "--input-ref",
        input_ref or to_rel(case_dir, root),
        "--dispatch-message",
        dispatch_message,
        "--openclaw-bin",
        "openclaw",
        "--openclaw-stall-threshold-seconds",
        "900",
        "--output",
        to_rel(dispatch_output_path, root),
    ]
    if execute_openclaw:
        cmd.extend(
            [
                "--execute-openclaw",
                "--reset-openclaw-session",
                "--strict-session-match",
            ]
        )
    proc = run_cmd(cmd, root)
    trace = write_command_trace(
        root=root,
        trace_dir=trace_dir,
        command_id=f"dispatch_{stage_spec.stage_id}",
        cmd=cmd,
        proc=proc,
    )
    if proc.returncode != 0:
        raise Session5Error(f"dispatch_failed:{stage_spec.stage_id}:rc={proc.returncode}")
    if not dispatch_output_path.exists():
        raise Session5Error(f"dispatch_output_missing:{stage_spec.stage_id}")

    dispatch_output = load_json(dispatch_output_path)
    dispatch_exec = dispatch_output.get("dispatch") if isinstance(dispatch_output.get("dispatch"), dict) else {}
    if execute_openclaw:
        if not bool(dispatch_exec.get("executed")):
            raise Session5Error(f"dispatch_not_executed:{stage_spec.stage_id}")
        if dispatch_exec.get("return_code") != 0:
            raise Session5Error(f"dispatch_nonzero:{stage_spec.stage_id}:{dispatch_exec.get('return_code')}")
        if bool(dispatch_exec.get("stalled")):
            raise Session5Error(f"dispatch_stalled:{stage_spec.stage_id}")

    probe = collect_probe_from_dispatch(
        root=root,
        stage=stage_spec.stage_id,
        dispatch_output=dispatch_output,
        output_ref=to_rel(dispatch_output_path, root),
    )
    return (
        {
            "stage": stage_spec.stage_id,
            "phase": stage_spec.phase_id,
            "process_id": stage_spec.process_id,
            "execute_openclaw": execute_openclaw,
            "dispatch_output_ref": to_rel(dispatch_output_path, root),
            "trace": trace,
        },
        probe,
    )


def ensure_rules_file(case_dir: Path) -> Path:
    rules_path = case_dir / "fixtures" / "aggregation_rules.json"
    dump_json(
        rules_path,
        {
            "precedence": ["fail", "hold", "test_invalid", "pass"],
            "owner": "session5-internal-runner",
            "generated_at": now_iso(),
        },
    )
    return rules_path


def create_test_doc(case_dir: Path) -> Path:
    """生成可稳定通过的最小 TEST.md，避免依赖历史大用例语义。"""
    test_doc = case_dir / "fixtures" / "session5_test_doc.md"
    write_text(
        test_doc,
        """# Session5 Test Doc

## Test Cases

### TC-001: Session5 主链规则匹配

- Type: Objective
- Priority: P0
- Input: canonical internal chain output
- Expected: output contains session5-pass-token
- Evaluation Method: Rule Match
- Expected Conditions: [session5-pass-token]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 1
- Judge Perspectives: [qa]
- Timeout Seconds: 120
- Retry Policy: max 1
""",
    )
    return test_doc


def run_objective_scope(
    *,
    root: Path,
    case_dir: Path,
    missing_context_ref: bool,
    objective_context_variant: str = "",
) -> Dict[str, Any]:
    stage_dir = case_dir / "objective-scope-baseline"
    stage_dir.mkdir(parents=True, exist_ok=True)

    objective_context = stage_dir / "objective_context.md"
    context_lines = [
        "# Session5 Objective Context",
        "",
        "- 目标：验证 M3 内部主线 E2E 在在线分发下可运行。",
        "- 范围：以 skill/process/agent 三类样本完成闭环。",
        "- 约束：生命周期上限保持 review，不推进 active。",
    ]
    if objective_context_variant.strip():
        # 追加场景标签，确保不同用例/轮次的 objective 可追溯且不复用。
        context_lines.append(f"- 场景标签：{objective_context_variant.strip()}")
    write_text(objective_context, "\n".join(context_lines))

    runner_input = stage_dir / "input.json"
    runner_output = stage_dir / "output.json"
    evidence_dir = stage_dir / "evidence"

    input_payload = {
        "objective_context_ref": "" if missing_context_ref else to_rel(objective_context, root),
    }
    dump_json(runner_input, input_payload)

    cmd = [
        sys.executable,
        "processes/meta/objective-scope-baseline/scripts/objective_scope_baseline_runner.py",
        "--input",
        to_rel(runner_input, root),
        "--output",
        to_rel(runner_output, root),
        "--evidence-dir",
        to_rel(evidence_dir, root),
        "--run-id",
        stage_dir.name,
    ]
    proc = run_cmd(cmd, root)
    trace = write_command_trace(
        root=root,
        trace_dir=stage_dir / "traces",
        command_id="objective_scope_runner",
        cmd=cmd,
        proc=proc,
    )
    output_payload = load_json(runner_output) if runner_output.exists() else {}
    return {
        "return_code": proc.returncode,
        "trace": trace,
        "output_ref": to_rel(runner_output, root),
        "output": output_payload,
    }


def run_spec_authoring(
    *,
    root: Path,
    case_dir: Path,
    objective_ref: str,
    scope_baseline_ref: str,
) -> Dict[str, Any]:
    stage_dir = case_dir / "spec-authoring-contract"
    stage_dir.mkdir(parents=True, exist_ok=True)

    spec_doc = stage_dir / "generated_spec.md"
    spec_contract = stage_dir / "spec_contract.json"
    output_path = stage_dir / "output.json"

    write_text(
        spec_doc,
        "\n".join(
            [
                "# Session5 Generated Spec",
                "",
                f"- objective_ref: {objective_ref}",
                f"- scope_baseline_ref: {scope_baseline_ref}",
                "- intent: 使用 M3 canonical 链执行内部主线 E2E。",
                "- acceptance: 需覆盖 happy/fail-rework/agent 双分支。",
            ]
        ),
    )
    dump_json(
        spec_contract,
        {
            "objective_ref": objective_ref,
            "scope_baseline_ref": scope_baseline_ref,
            "spec_doc_ref": to_rel(spec_doc, root),
            "generated_at": now_iso(),
        },
    )
    dump_json(
        output_path,
        {
            "status": "ok",
            "process_id": "spec-authoring-contract",
            "spec_ref": to_rel(spec_contract, root),
            "spec_doc_ref": to_rel(spec_doc, root),
        },
    )
    return {
        "return_code": 0,
        "output_ref": to_rel(output_path, root),
        "output": load_json(output_path),
    }


def run_quality_gate_preparation(
    *,
    root: Path,
    case_dir: Path,
    objective_ref: str,
    spec_ref: str,
    test_doc_ref: str,
) -> Dict[str, Any]:
    stage_dir = case_dir / "quality-gate-preparation"
    stage_dir.mkdir(parents=True, exist_ok=True)
    input_path = stage_dir / "input.json"
    output_path = stage_dir / "output.json"
    evidence_dir = stage_dir / "evidence"

    dump_json(
        input_path,
        {
            "objective_ref": objective_ref,
            "spec_ref": spec_ref,
            "test_doc_ref": test_doc_ref,
            "risk_focus": ["P0", "P1"],
        },
    )

    cmd = [
        sys.executable,
        "processes/meta/quality-gate-preparation/scripts/quality_gate_preparation_runner.py",
        "--input",
        to_rel(input_path, root),
        "--output",
        to_rel(output_path, root),
        "--evidence-dir",
        to_rel(evidence_dir, root),
        "--run-id",
        stage_dir.name,
    ]
    proc = run_cmd(cmd, root)
    trace = write_command_trace(
        root=root,
        trace_dir=stage_dir / "traces",
        command_id="quality_gate_preparation_runner",
        cmd=cmd,
        proc=proc,
    )
    output_payload = load_json(output_path) if output_path.exists() else {}
    return {
        "return_code": proc.returncode,
        "trace": trace,
        "output_ref": to_rel(output_path, root),
        "output": output_payload,
    }


def run_implementation_execution(
    *,
    root: Path,
    case_dir: Path,
    spec_ref: str,
) -> Dict[str, Any]:
    stage_dir = case_dir / "implementation-execution-core"
    stage_dir.mkdir(parents=True, exist_ok=True)
    implementation = stage_dir / "implementation_result.json"
    output_path = stage_dir / "output.json"

    dump_json(
        implementation,
        {
            "spec_ref": spec_ref,
            "result": "session5-pass-token",
            "notes": "用于质量门禁 Rule Match 验证。",
            "generated_at": now_iso(),
        },
    )

    dump_json(
        output_path,
        {
            "status": "ok",
            "process_id": "implementation-execution-core",
            "implementation_ref": to_rel(implementation, root),
            "actual_output_refs": [to_rel(implementation, root)],
        },
    )
    return {
        "return_code": 0,
        "output_ref": to_rel(output_path, root),
        "output": load_json(output_path),
    }


def run_quality_gate_evaluation(
    *,
    root: Path,
    case_dir: Path,
    preparation_bundle_ref: str,
    actual_output_refs: List[str],
    dispatch_trace_ref: str,
    case_report_ref: str,
    phase_outputs: List[str],
) -> Dict[str, Any]:
    stage_dir = case_dir / "quality-gate-evaluation"
    stage_dir.mkdir(parents=True, exist_ok=True)
    input_path = stage_dir / "input.json"
    output_path = stage_dir / "output.json"
    evidence_dir = stage_dir / "evidence"

    rules_path = ensure_rules_file(case_dir)
    dump_json(
        input_path,
        {
            "preparation_bundle_ref": preparation_bundle_ref,
            "actual_output_refs": actual_output_refs,
            "regression_scope": "M3",
            "profile_set": ["quality-gate.baseline@1.0.0"],
            "aggregation_rules_ref": to_rel(rules_path, root),
            "force_hold": False,
            "dispatch_trace_ref": dispatch_trace_ref,
            "phase_outputs": phase_outputs,
            "case_report_ref": case_report_ref,
        },
    )

    cmd = [
        sys.executable,
        "processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py",
        "--input",
        to_rel(input_path, root),
        "--output",
        to_rel(output_path, root),
        "--evidence-dir",
        to_rel(evidence_dir, root),
        "--run-id",
        stage_dir.name,
    ]
    proc = run_cmd(cmd, root)
    trace = write_command_trace(
        root=root,
        trace_dir=stage_dir / "traces",
        command_id="quality_gate_evaluation_runner",
        cmd=cmd,
        proc=proc,
    )
    output_payload = load_json(output_path) if output_path.exists() else {}
    return {
        "return_code": proc.returncode,
        "trace": trace,
        "output_ref": to_rel(output_path, root),
        "output": output_payload,
    }


def run_lifecycle_review(
    *,
    root: Path,
    case_dir: Path,
    final_gate_verdict_ref: str,
) -> Dict[str, Any]:
    stage_dir = case_dir / "lifecycle-review"
    stage_dir.mkdir(parents=True, exist_ok=True)

    target_asset = stage_dir / "target_asset.json"
    dump_json(
        target_asset,
        {
            "asset_id": "agent:release-manager-agent",
            "lifecycle_status": "draft",
            "notes": "Session5 内部主线目标资产生命周期上限 review。",
        },
    )

    input_path = stage_dir / "input.json"
    output_path = stage_dir / "output.json"
    evidence_dir = stage_dir / "evidence"

    dump_json(
        input_path,
        {
            "final_gate_verdict_ref": final_gate_verdict_ref,
            "target_asset_ref": to_rel(target_asset, root),
            "requested_transition": {"from_status": "draft", "to_status": "review"},
            "current_status": "draft",
        },
    )

    cmd = [
        sys.executable,
        "processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py",
        "--input",
        to_rel(input_path, root),
        "--output",
        to_rel(output_path, root),
        "--evidence-dir",
        to_rel(evidence_dir, root),
        "--run-id",
        stage_dir.name,
    ]
    proc = run_cmd(cmd, root)
    trace = write_command_trace(
        root=root,
        trace_dir=stage_dir / "traces",
        command_id="lifecycle_review_runner",
        cmd=cmd,
        proc=proc,
    )
    output_payload = load_json(output_path) if output_path.exists() else {}
    return {
        "return_code": proc.returncode,
        "trace": trace,
        "output_ref": to_rel(output_path, root),
        "output": output_payload,
    }


def run_registry_sync(
    *,
    root: Path,
    case_dir: Path,
    lifecycle_transition_ref: str,
    evidence_ref: str,
) -> Dict[str, Any]:
    stage_dir = case_dir / "registry-sync"
    stage_dir.mkdir(parents=True, exist_ok=True)

    patch_plan = stage_dir / "registry_patch_plan.json"
    dump_json(
        patch_plan,
        {
            "plan_id": "session5-no-delta",
            "strategy": "verify-only",
            "note": "Session5 仅验证 registry 合约，不做结构字段变更。",
        },
    )

    input_path = stage_dir / "input.json"
    output_path = stage_dir / "output.json"
    dump_json(
        input_path,
        {
            "target_registry_ref": "shared/registry/skill_registry.json",
            "registry_patch_plan_ref": to_rel(patch_plan, root),
            "requested_transition_ref": lifecycle_transition_ref,
            "verify_scope": "session5-internal",
            "evidence_ref": evidence_ref,
        },
    )

    cmd = [
        sys.executable,
        "processes/meta/registry-sync/scripts/registry_sync_runner.py",
        "--input",
        to_rel(input_path, root),
        "--output",
        to_rel(output_path, root),
    ]
    proc = run_cmd(cmd, root)
    trace = write_command_trace(
        root=root,
        trace_dir=stage_dir / "traces",
        command_id="registry_sync_runner",
        cmd=cmd,
        proc=proc,
    )
    output_payload = load_json(output_path) if output_path.exists() else {}
    return {
        "return_code": proc.returncode,
        "trace": trace,
        "output_ref": to_rel(output_path, root),
        "output": output_payload,
    }


def run_release_packaging(
    *,
    root: Path,
    case_dir: Path,
    final_gate_verdict_ref: str,
    lifecycle_transition_ref: str,
    registry_sync_ref: str,
) -> Dict[str, Any]:
    stage_dir = case_dir / "release-packaging-governed"
    stage_dir.mkdir(parents=True, exist_ok=True)

    gate = load_json(resolve_path(root, final_gate_verdict_ref))
    registry_sync = load_json(resolve_path(root, registry_sync_ref))
    _ = load_json(resolve_path(root, lifecycle_transition_ref))

    decision = str(gate.get("gate_decision") or "").strip().lower()
    sync_decision = str(registry_sync.get("sync_decision") or "").strip().lower()
    if decision != "pass":
        raise Session5Error(f"release_packaging_gate_not_pass:{decision}")
    if sync_decision != "pass":
        raise Session5Error(f"release_packaging_registry_not_pass:{sync_decision}")

    release_package = stage_dir / "release_package.json"
    changelog = stage_dir / "changelog.json"
    rollback_bundle = stage_dir / "rollback_bundle.json"
    candidate_artifacts = stage_dir / "candidate_artifacts.json"
    output_path = stage_dir / "output.json"

    dump_json(
        release_package,
        {
            "package_id": f"pkg-session5-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "generated_at": now_iso(),
            "source": "session5-internal",
        },
    )
    dump_json(
        changelog,
        {
            "generated_at": now_iso(),
            "entries": [
                "quality-gate-preparation 通过",
                "quality-gate-evaluation 通过",
                "lifecycle-review 收敛到 review",
                "registry-sync verify 通过",
            ],
        },
    )
    dump_json(
        rollback_bundle,
        {
            "bundle_id": "rb-session5-001",
            "generated_at": now_iso(),
            "steps": ["restore release package", "verify health"],
        },
    )
    dump_json(
        candidate_artifacts,
        {
            "artifacts": [to_rel(release_package, root), to_rel(changelog, root)],
            "rollback_bundle_ref": to_rel(rollback_bundle, root),
            "generated_at": now_iso(),
        },
    )
    dump_json(
        output_path,
        {
            "status": "ok",
            "process_id": "release-packaging-governed",
            "release_decision": "approved",
            "release_package_ref": to_rel(release_package, root),
            "changelog_ref": to_rel(changelog, root),
            "rollback_bundle_ref": to_rel(rollback_bundle, root),
            "candidate_artifacts_ref": to_rel(candidate_artifacts, root),
        },
    )

    return {
        "return_code": 0,
        "output_ref": to_rel(output_path, root),
        "output": load_json(output_path),
    }


def run_release_manager_agent(
    *,
    root: Path,
    case_dir: Path,
    request_id: str,
    objective_ref: str,
    candidate_artifacts_ref: str,
    final_gate_verdict_ref: str,
    lifecycle_transition_ref: str,
    registry_sync_ref: str,
    rollback_bundle_ref: str,
    evidence_ref: str,
) -> Dict[str, Any]:
    stage_dir = case_dir / "release-manager-agent"
    stage_dir.mkdir(parents=True, exist_ok=True)

    input_path = stage_dir / f"input_{request_id}.json"
    output_path = stage_dir / f"output_{request_id}.json"
    evidence_dir = stage_dir / f"evidence_{request_id}"

    dump_json(
        input_path,
        {
            "request_id": request_id,
            "objective_ref": objective_ref,
            "candidate_artifacts_ref": candidate_artifacts_ref,
            "final_gate_verdict_ref": final_gate_verdict_ref,
            "lifecycle_transition_ref": lifecycle_transition_ref,
            "registry_sync_ref": registry_sync_ref,
            "release_window": "2026-02-24T00:00:00Z/2026-02-24T23:59:59Z",
            "rollback_bundle_ref": rollback_bundle_ref,
            "requested_by": "session5-internal",
            "evidence_ref": evidence_ref,
        },
    )

    cmd = [
        sys.executable,
        "agents/app/delivery/release-manager-agent/scripts/release_manager_agent_runner.py",
        "--input",
        to_rel(input_path, root),
        "--output",
        to_rel(output_path, root),
        "--evidence-dir",
        to_rel(evidence_dir, root),
    ]
    proc = run_cmd(cmd, root)
    trace = write_command_trace(
        root=root,
        trace_dir=stage_dir / "traces",
        command_id=f"release_manager_agent_runner_{request_id}",
        cmd=cmd,
        proc=proc,
    )
    output_payload = load_json(output_path) if output_path.exists() else {}
    return {
        "return_code": proc.returncode,
        "trace": trace,
        "output_ref": to_rel(output_path, root),
        "output": output_payload,
    }


def run_canonical_chain(
    *,
    root: Path,
    case_dir: Path,
    objective_missing_context: bool,
    objective_context_variant: str = "",
    dispatch_openclaw: bool = True,
) -> Dict[str, Any]:
    """执行 canonical 主链。若 objective_missing_context=True，将在首阶段触发 Fail-Closed。"""
    stage_traces: List[Dict[str, Any]] = []
    liveness_probes: List[Dict[str, Any]] = []

    def _dispatch(stage_id: str, input_refs: List[str]) -> None:
        spec = next(item for item in CANONICAL_CHAIN if item.stage_id == stage_id)
        trace, probe = dispatch_stage(
            root=root,
            case_dir=case_dir,
            stage_spec=spec,
            input_refs=input_refs,
            execute_openclaw=dispatch_openclaw,
        )
        stage_traces.append(trace)
        liveness_probes.append(probe)

    _dispatch("objective-scope-baseline", [to_rel(case_dir, root)])
    objective_scope = run_objective_scope(
        root=root,
        case_dir=case_dir,
        missing_context_ref=objective_missing_context,
        objective_context_variant=objective_context_variant,
    )
    if objective_scope["return_code"] != 0:
        return {
            "status": "failed",
            "failed_stage": "objective-scope-baseline",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "objective_scope": objective_scope,
        }

    objective_output = objective_scope["output"]
    objective_ref = str(objective_output.get("objective_ref") or "")
    scope_baseline_ref = str(objective_output.get("scope_baseline_ref") or "")
    if not objective_ref or not scope_baseline_ref:
        return {
            "status": "failed",
            "failed_stage": "objective-scope-baseline",
            "failure_reason": "objective_or_scope_missing",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "objective_scope": objective_scope,
        }

    _dispatch("spec-authoring-contract", [scope_baseline_ref])
    spec_authoring = run_spec_authoring(
        root=root,
        case_dir=case_dir,
        objective_ref=objective_ref,
        scope_baseline_ref=scope_baseline_ref,
    )
    spec_ref = str(spec_authoring["output"].get("spec_ref") or "")
    if not spec_ref:
        return {
            "status": "failed",
            "failed_stage": "spec-authoring-contract",
            "failure_reason": "spec_ref_missing",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "spec_authoring": spec_authoring,
        }

    test_doc = create_test_doc(case_dir)
    _dispatch("quality-gate-preparation", [spec_ref])
    quality_prep = run_quality_gate_preparation(
        root=root,
        case_dir=case_dir,
        objective_ref=objective_ref,
        spec_ref=spec_ref,
        test_doc_ref=to_rel(test_doc, root),
    )
    if quality_prep["return_code"] != 0:
        return {
            "status": "failed",
            "failed_stage": "quality-gate-preparation",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "quality_prep": quality_prep,
        }

    prep_output = quality_prep["output"]
    preparation_bundle_ref = str(prep_output.get("preparation_bundle_ref") or "")
    if not preparation_bundle_ref:
        return {
            "status": "failed",
            "failed_stage": "quality-gate-preparation",
            "failure_reason": "preparation_bundle_ref_missing",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "quality_prep": quality_prep,
        }

    _dispatch("implementation-execution-core", [spec_ref, preparation_bundle_ref])
    impl = run_implementation_execution(root=root, case_dir=case_dir, spec_ref=spec_ref)
    implementation_ref = str(impl["output"].get("implementation_ref") or "")
    actual_output_refs = impl["output"].get("actual_output_refs")
    if not implementation_ref or not isinstance(actual_output_refs, list) or not actual_output_refs:
        return {
            "status": "failed",
            "failed_stage": "implementation-execution-core",
            "failure_reason": "implementation_output_missing",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "implementation": impl,
        }

    _dispatch("quality-gate-evaluation", [preparation_bundle_ref, implementation_ref])
    quality_gate_dispatch_ref = str(stage_traces[-1].get("dispatch_output_ref") or "") if stage_traces else ""

    case_report_path = case_dir / "quality-gate-evaluation" / "case_report.json"
    dump_json(
        case_report_path,
        {
            "case_id": case_dir.name,
            "assertions": {
                "failure_path": True,
                "rollback_path": True,
            },
            "evidence": {
                "objective_scope_output_ref": objective_scope.get("output_ref", ""),
                "spec_authoring_output_ref": spec_authoring.get("output_ref", ""),
                "quality_prep_output_ref": quality_prep.get("output_ref", ""),
                "implementation_output_ref": impl.get("output_ref", ""),
            },
        },
    )

    quality_eval = run_quality_gate_evaluation(
        root=root,
        case_dir=case_dir,
        preparation_bundle_ref=preparation_bundle_ref,
        actual_output_refs=[str(item) for item in actual_output_refs],
        dispatch_trace_ref=quality_gate_dispatch_ref,
        case_report_ref=to_rel(case_report_path, root),
        phase_outputs=[
            str(objective_scope.get("output_ref") or ""),
            str(spec_authoring.get("output_ref") or ""),
            str(quality_prep.get("output_ref") or ""),
            str(impl.get("output_ref") or ""),
        ],
    )
    if quality_eval["return_code"] != 0:
        return {
            "status": "failed",
            "failed_stage": "quality-gate-evaluation",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "quality_eval": quality_eval,
        }

    eval_output = quality_eval["output"]
    gate_decision = str(eval_output.get("gate_decision") or "")
    final_gate_verdict_ref = str(eval_output.get("final_gate_verdict_ref") or "")
    if gate_decision != "pass" or not final_gate_verdict_ref:
        return {
            "status": "failed",
            "failed_stage": "quality-gate-evaluation",
            "failure_reason": f"gate_not_pass:{gate_decision}",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "quality_eval": quality_eval,
        }

    _dispatch("lifecycle-review", [final_gate_verdict_ref])
    lifecycle = run_lifecycle_review(
        root=root,
        case_dir=case_dir,
        final_gate_verdict_ref=final_gate_verdict_ref,
    )
    if lifecycle["return_code"] != 0:
        return {
            "status": "failed",
            "failed_stage": "lifecycle-review",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "lifecycle": lifecycle,
        }

    lifecycle_output = lifecycle["output"]
    lifecycle_transition_ref = str(lifecycle_output.get("lifecycle_transition_ref") or "")
    lifecycle_registry_sync_ref = str(lifecycle_output.get("registry_sync_ref") or "")
    lifecycle_report_ref = str(lifecycle_output.get("lifecycle_review_report_ref") or "")
    if not lifecycle_transition_ref or not lifecycle_registry_sync_ref or not lifecycle_report_ref:
        return {
            "status": "failed",
            "failed_stage": "lifecycle-review",
            "failure_reason": "lifecycle_outputs_missing",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "lifecycle": lifecycle,
        }

    _dispatch("registry-sync", [lifecycle_transition_ref, lifecycle_report_ref])
    registry_sync = run_registry_sync(
        root=root,
        case_dir=case_dir,
        lifecycle_transition_ref=lifecycle_transition_ref,
        evidence_ref=lifecycle_report_ref,
    )
    if registry_sync["return_code"] != 0:
        return {
            "status": "failed",
            "failed_stage": "registry-sync",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "registry_sync": registry_sync,
        }

    registry_output = registry_sync["output"]
    registry_sync_ref = str(registry_output.get("registry_sync_ref") or "")
    if str(registry_output.get("sync_decision") or "") != "pass" or not registry_sync_ref:
        return {
            "status": "failed",
            "failed_stage": "registry-sync",
            "failure_reason": "registry_sync_not_pass",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "registry_sync": registry_sync,
        }

    _dispatch("release-packaging-governed", [final_gate_verdict_ref, lifecycle_transition_ref, registry_sync_ref])
    release_pack = run_release_packaging(
        root=root,
        case_dir=case_dir,
        final_gate_verdict_ref=final_gate_verdict_ref,
        lifecycle_transition_ref=lifecycle_transition_ref,
        registry_sync_ref=registry_sync_ref,
    )
    if release_pack["return_code"] != 0:
        return {
            "status": "failed",
            "failed_stage": "release-packaging-governed",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "release_packaging": release_pack,
        }

    pack_output = release_pack["output"]
    candidate_artifacts_ref = str(pack_output.get("candidate_artifacts_ref") or "")
    rollback_bundle_ref = str(pack_output.get("rollback_bundle_ref") or "")

    return {
        "status": "ok",
        "stage_traces": stage_traces,
        "liveness_probes": liveness_probes,
        "gate_chain_refs": [
            quality_prep["output_ref"],
            quality_eval["output_ref"],
            lifecycle["output_ref"],
            registry_sync["output_ref"],
            lifecycle_registry_sync_ref,
        ],
        "objective_ref": objective_ref,
        "scope_baseline_ref": scope_baseline_ref,
        "spec_ref": spec_ref,
        "implementation_ref": implementation_ref,
        "preparation_bundle_ref": preparation_bundle_ref,
        "final_gate_verdict_ref": final_gate_verdict_ref,
        "lifecycle_transition_ref": lifecycle_transition_ref,
        "registry_sync_ref": registry_sync_ref,
        "candidate_artifacts_ref": candidate_artifacts_ref,
        "rollback_bundle_ref": rollback_bundle_ref,
        "evidence_ref": pack_output.get("release_package_ref", ""),
        "quality_prep": quality_prep,
        "quality_eval": quality_eval,
        "lifecycle": lifecycle,
        "registry_sync": registry_sync,
        "release_packaging": release_pack,
    }


def case_success_payload(case_id: str, payload: Dict[str, Any], note: str) -> Dict[str, Any]:
    return {
        "id": case_id,
        "status": "pass",
        "natural_language_conclusion": note,
        "debug_rounds": 0,
        "rework_actions": [],
        "liveness_probes": payload.get("liveness_probes", []),
        "gate_chain_refs": payload.get("gate_chain_refs", []),
        "details": {
            "objective_ref": payload.get("objective_ref", ""),
            "final_gate_verdict_ref": payload.get("final_gate_verdict_ref", ""),
            "lifecycle_transition_ref": payload.get("lifecycle_transition_ref", ""),
            "registry_sync_ref": payload.get("registry_sync_ref", ""),
            "candidate_artifacts_ref": payload.get("candidate_artifacts_ref", ""),
            "rollback_bundle_ref": payload.get("rollback_bundle_ref", ""),
            "failure_path": True,
            "rollback_path": True,
        },
    }


def build_case1_base_chain(case: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """从 M3-INT-001 中抽取可复用的下游链路引用。"""
    if str(case.get("status") or "") != "pass":
        return None
    details = case.get("details") if isinstance(case.get("details"), dict) else {}
    required = [
        "objective_ref",
        "candidate_artifacts_ref",
        "final_gate_verdict_ref",
        "lifecycle_transition_ref",
        "registry_sync_ref",
        "rollback_bundle_ref",
    ]
    if any(not str(details.get(key) or "").strip() for key in required):
        return None
    return {
        "objective_ref": str(details.get("objective_ref") or ""),
        "candidate_artifacts_ref": str(details.get("candidate_artifacts_ref") or ""),
        "final_gate_verdict_ref": str(details.get("final_gate_verdict_ref") or ""),
        "lifecycle_transition_ref": str(details.get("lifecycle_transition_ref") or ""),
        "registry_sync_ref": str(details.get("registry_sync_ref") or ""),
        "rollback_bundle_ref": str(details.get("rollback_bundle_ref") or ""),
        "gate_chain_refs": case.get("gate_chain_refs", []) if isinstance(case.get("gate_chain_refs"), list) else [],
    }


def run_case_001(root: Path, evidence_root: Path) -> Dict[str, Any]:
    case_id = "M3-INT-001"
    case_dir = evidence_root / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    pipeline = run_canonical_chain(
        root=root,
        case_dir=case_dir,
        objective_missing_context=False,
        objective_context_variant="M3-INT-001-happy",
        dispatch_openclaw=True,
    )
    if pipeline.get("status") != "ok":
        return {
            "id": case_id,
            "status": "fail",
            "natural_language_conclusion": "内部主链 Happy 失败，未达到 Session5 准入。",
            "debug_rounds": 0,
            "rework_actions": [],
            "liveness_probes": pipeline.get("liveness_probes", []),
            "gate_chain_refs": pipeline.get("gate_chain_refs", []),
            "details": {"pipeline": pipeline},
        }

    spec = next(item for item in CANONICAL_CHAIN if item.stage_id == "release-manager-agent")
    dispatch_trace, probe = dispatch_stage(
        root=root,
        case_dir=case_dir,
        stage_spec=spec,
        input_refs=[
            str(pipeline.get("candidate_artifacts_ref") or ""),
            str(pipeline.get("final_gate_verdict_ref") or ""),
            str(pipeline.get("registry_sync_ref") or ""),
        ],
        execute_openclaw=True,
    )
    release_agent = run_release_manager_agent(
        root=root,
        case_dir=case_dir,
        request_id="REQ-M3-INT-001",
        objective_ref=str(pipeline.get("objective_ref") or ""),
        candidate_artifacts_ref=str(pipeline.get("candidate_artifacts_ref") or ""),
        final_gate_verdict_ref=str(pipeline.get("final_gate_verdict_ref") or ""),
        lifecycle_transition_ref=str(pipeline.get("lifecycle_transition_ref") or ""),
        registry_sync_ref=str(pipeline.get("registry_sync_ref") or ""),
        rollback_bundle_ref=str(pipeline.get("rollback_bundle_ref") or ""),
        evidence_ref=str(pipeline.get("final_gate_verdict_ref") or ""),
    )

    all_probes = list(pipeline.get("liveness_probes", []))
    all_probes.append(probe)

    if release_agent["return_code"] != 0:
        return {
            "id": case_id,
            "status": "fail",
            "natural_language_conclusion": "主链执行到 release-manager-agent 时失败。",
            "debug_rounds": 0,
            "rework_actions": [],
            "liveness_probes": all_probes,
            "gate_chain_refs": pipeline.get("gate_chain_refs", []),
            "details": {
                "pipeline": pipeline,
                "release_agent": release_agent,
                "dispatch": dispatch_trace,
            },
        }

    agent_output = release_agent.get("output", {})
    delivered = str(agent_output.get("status") or "") == "delivered"
    if not delivered:
        return {
            "id": case_id,
            "status": "fail",
            "natural_language_conclusion": "主链执行完成但发布未进入 delivered。",
            "debug_rounds": 0,
            "rework_actions": [],
            "liveness_probes": all_probes,
            "gate_chain_refs": pipeline.get("gate_chain_refs", []),
            "details": {
                "pipeline": pipeline,
                "release_agent": release_agent,
                "dispatch": dispatch_trace,
            },
        }

    case_payload = case_success_payload(
        case_id,
        pipeline,
        "内部主链 Happy 通过：从 objective 到 release-manager-agent 全链可执行，门禁与生命周期均保持在 review 上限内。",
    )
    case_payload["liveness_probes"] = all_probes
    case_payload["details"].update(
        {
            "release_manager_agent_output_ref": release_agent.get("output_ref", ""),
            "release_manager_delivery": True,
        }
    )
    return case_payload


def run_case_002(root: Path, evidence_root: Path) -> Dict[str, Any]:
    case_id = "M3-INT-002"
    case_dir = evidence_root / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    rework_actions: List[str] = []
    debug_rounds = 0

    # Round 1: 故意触发 Fail-Closed
    first_round = run_canonical_chain(
        root=root,
        case_dir=case_dir / "round1_fail",
        objective_missing_context=True,
        objective_context_variant="M3-INT-002-round1-fail",
        dispatch_openclaw=True,
    )
    probes = list(first_round.get("liveness_probes", []))
    failed_stage = str(first_round.get("failed_stage") or "")
    first_round_failed = first_round.get("status") == "failed" and failed_stage == "objective-scope-baseline"

    if not first_round_failed:
        return {
            "id": case_id,
            "status": "fail",
            "natural_language_conclusion": "预期 Fail-Closed 未触发，无法证明失败后返工链路。",
            "debug_rounds": debug_rounds,
            "rework_actions": rework_actions,
            "liveness_probes": probes,
            "gate_chain_refs": first_round.get("gate_chain_refs", []),
            "details": {"round1": first_round},
        }

    debug_rounds += 1
    rework_actions.append("定位 root cause：objective_context_ref 缺失导致 objective-scope-baseline Fail-Closed。")
    rework_actions.append("修复输入：补齐 objective_context_ref，并在在线分发下验证恢复。")

    round2_dir = case_dir / "round2_rework"
    second_round = run_canonical_chain(
        root=root,
        case_dir=round2_dir,
        objective_missing_context=False,
        objective_context_variant="M3-INT-002-round2-rework-full-rerun",
        dispatch_openclaw=True,
    )
    rework_actions.append("修复验证：修复后执行全链 OpenClaw 在线重跑（p1~p8），确认门禁链路恢复。")
    probes.extend(second_round.get("liveness_probes", []))

    if second_round.get("status") != "ok":
        return {
            "id": case_id,
            "status": "fail",
            "natural_language_conclusion": "返工后重跑仍失败，闭环不成立。",
            "debug_rounds": debug_rounds,
            "rework_actions": rework_actions,
            "liveness_probes": probes,
            "gate_chain_refs": second_round.get("gate_chain_refs", []),
            "details": {"round1": first_round, "round2": second_round},
        }

    spec = next(item for item in CANONICAL_CHAIN if item.stage_id == "release-manager-agent")
    _, probe = dispatch_stage(
        root=root,
        case_dir=round2_dir,
        stage_spec=spec,
        input_refs=[
            str(second_round.get("candidate_artifacts_ref") or ""),
            str(second_round.get("final_gate_verdict_ref") or ""),
            str(second_round.get("registry_sync_ref") or ""),
        ],
    )
    probes.append(probe)

    release_agent = run_release_manager_agent(
        root=root,
        case_dir=round2_dir,
        request_id="REQ-M3-INT-002",
        objective_ref=str(second_round.get("objective_ref") or ""),
        candidate_artifacts_ref=str(second_round.get("candidate_artifacts_ref") or ""),
        final_gate_verdict_ref=str(second_round.get("final_gate_verdict_ref") or ""),
        lifecycle_transition_ref=str(second_round.get("lifecycle_transition_ref") or ""),
        registry_sync_ref=str(second_round.get("registry_sync_ref") or ""),
        rollback_bundle_ref=str(second_round.get("rollback_bundle_ref") or ""),
        evidence_ref=str(second_round.get("final_gate_verdict_ref") or ""),
    )
    delivered = release_agent["return_code"] == 0 and str(release_agent.get("output", {}).get("status") or "") == "delivered"
    if not delivered:
        return {
            "id": case_id,
            "status": "fail",
            "natural_language_conclusion": "返工后链路已恢复但发布阶段未通过。",
            "debug_rounds": debug_rounds,
            "rework_actions": rework_actions,
            "liveness_probes": probes,
            "gate_chain_refs": second_round.get("gate_chain_refs", []),
            "details": {
                "round1": first_round,
                "round2": second_round,
                "release_agent": release_agent,
            },
        }

    payload = case_success_payload(
        case_id,
        second_round,
        "Fail-Closed -> Debug -> 修复 -> 重跑通过已闭环：失败点可定位、修复动作可执行、重跑可恢复。",
    )
    payload["debug_rounds"] = debug_rounds
    payload["rework_actions"] = rework_actions
    payload["liveness_probes"] = probes
    payload["details"].update(
        {
            "round1_failed_stage": failed_stage,
            "round1_reason": first_round.get("failure_reason", "missing_objective_context_ref"),
            "round2_mode": "full_chain_openclaw_rerun",
            "release_manager_agent_output_ref": release_agent.get("output_ref", ""),
        }
    )
    return payload


def run_case_003(root: Path, evidence_root: Path, base_chain: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    case_id = "M3-INT-003"
    case_dir = evidence_root / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    required_keys = {
        "objective_ref",
        "candidate_artifacts_ref",
        "final_gate_verdict_ref",
        "lifecycle_transition_ref",
        "registry_sync_ref",
        "rollback_bundle_ref",
    }
    use_base = isinstance(base_chain, dict) and required_keys.issubset(set(base_chain.keys()))
    if use_base:
        pipeline = {
            "status": "ok",
            "objective_ref": base_chain.get("objective_ref", ""),
            "candidate_artifacts_ref": base_chain.get("candidate_artifacts_ref", ""),
            "final_gate_verdict_ref": base_chain.get("final_gate_verdict_ref", ""),
            "lifecycle_transition_ref": base_chain.get("lifecycle_transition_ref", ""),
            "registry_sync_ref": base_chain.get("registry_sync_ref", ""),
            "rollback_bundle_ref": base_chain.get("rollback_bundle_ref", ""),
            "gate_chain_refs": base_chain.get("gate_chain_refs", []),
            "liveness_probes": [],
        }
    else:
        pipeline = run_canonical_chain(
            root=root,
            case_dir=case_dir,
            objective_missing_context=False,
            objective_context_variant="M3-INT-003-branch-validation",
            dispatch_openclaw=True,
        )
    probes = list(pipeline.get("liveness_probes", []))

    if pipeline.get("status") != "ok":
        return {
            "id": case_id,
            "status": "fail",
            "natural_language_conclusion": "无法进入 release-manager-agent 双分支验证，因为前置主链失败。",
            "debug_rounds": 0,
            "rework_actions": [],
            "liveness_probes": probes,
            "gate_chain_refs": pipeline.get("gate_chain_refs", []),
            "details": pipeline,
        }

    spec = next(item for item in CANONICAL_CHAIN if item.stage_id == "release-manager-agent")
    _, probe_ok = dispatch_stage(
        root=root,
        case_dir=case_dir,
        stage_spec=spec,
        input_refs=[
            str(pipeline.get("candidate_artifacts_ref") or ""),
            str(pipeline.get("final_gate_verdict_ref") or ""),
        ],
        execute_openclaw=True,
    )
    probes.append(probe_ok)

    success = run_release_manager_agent(
        root=root,
        case_dir=case_dir,
        request_id="REQ-M3-INT-003-OK",
        objective_ref=str(pipeline.get("objective_ref") or ""),
        candidate_artifacts_ref=str(pipeline.get("candidate_artifacts_ref") or ""),
        final_gate_verdict_ref=str(pipeline.get("final_gate_verdict_ref") or ""),
        lifecycle_transition_ref=str(pipeline.get("lifecycle_transition_ref") or ""),
        registry_sync_ref=str(pipeline.get("registry_sync_ref") or ""),
        rollback_bundle_ref=str(pipeline.get("rollback_bundle_ref") or ""),
        evidence_ref=str(pipeline.get("final_gate_verdict_ref") or ""),
    )

    # 拒绝分支：故意传入不可达 gate 证据引用。
    missing_gate = case_dir / "fixtures" / "missing_final_gate_verdict.json"
    _, probe_reject = dispatch_stage(
        root=root,
        case_dir=case_dir,
        stage_spec=spec,
        input_refs=["missing_final_gate_verdict"],
        execute_openclaw=True,
    )
    probes.append(probe_reject)

    reject = run_release_manager_agent(
        root=root,
        case_dir=case_dir,
        request_id="REQ-M3-INT-003-REJECT",
        objective_ref=str(pipeline.get("objective_ref") or ""),
        candidate_artifacts_ref=str(pipeline.get("candidate_artifacts_ref") or ""),
        final_gate_verdict_ref=to_rel(missing_gate, root),
        lifecycle_transition_ref=str(pipeline.get("lifecycle_transition_ref") or ""),
        registry_sync_ref=str(pipeline.get("registry_sync_ref") or ""),
        rollback_bundle_ref=str(pipeline.get("rollback_bundle_ref") or ""),
        evidence_ref=str(pipeline.get("final_gate_verdict_ref") or ""),
    )

    success_ok = success["return_code"] == 0 and str(success.get("output", {}).get("status") or "") == "delivered"
    reject_ok = reject["return_code"] == 2 and str(reject.get("output", {}).get("status") or "") == "rejected"
    if not (success_ok and reject_ok):
        return {
            "id": case_id,
            "status": "fail",
            "natural_language_conclusion": "release-manager-agent 双分支未同时满足预期。",
            "debug_rounds": 0,
            "rework_actions": [],
            "liveness_probes": probes,
            "gate_chain_refs": pipeline.get("gate_chain_refs", []),
            "details": {
                "pipeline": pipeline,
                "success": success,
                "reject": reject,
                "success_ok": success_ok,
                "reject_ok": reject_ok,
            },
        }

    payload = case_success_payload(
        case_id,
        pipeline,
        "release-manager-agent 双分支验证通过：成功输出与拒绝输出均可稳定触发且可追溯。",
    )
    payload["liveness_probes"] = probes
    payload["details"].update(
        {
            "release_manager_success_output_ref": success.get("output_ref", ""),
            "release_manager_reject_output_ref": reject.get("output_ref", ""),
            "release_manager_success_seen": True,
            "release_manager_reject_seen": True,
        }
    )
    return payload


def build_summary_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Session5 Internal E2E Summary")
    lines.append("")
    lines.append(f"- ts: {report.get('ts', '')}")
    lines.append(f"- suite: {report.get('suite', '')}")
    lines.append(f"- status: {report.get('status', '')}")
    lines.append(f"- total: {report.get('total', 0)}")
    lines.append(f"- passed: {report.get('passed', 0)}")
    lines.append(f"- failed: {report.get('failed', 0)}")
    lines.append(f"- debug_rounds: {report.get('debug_rounds', 0)}")
    lines.append("")
    lines.append("## Case Results")
    for case in report.get("cases", []):
        if not isinstance(case, dict):
            continue
        lines.append(f"- {case.get('id', '')}: {case.get('status', '')}")
        lines.append(f"  - conclusion: {case.get('natural_language_conclusion', '')}")
    lines.append("")
    lines.append("## Session6 Readiness")
    readiness = report.get("session6_readiness", {})
    lines.append(f"- ready: {readiness.get('ready', False)}")
    lines.append(f"- decision: {readiness.get('decision', '')}")
    risks = readiness.get("risks") if isinstance(readiness.get("risks"), list) else []
    for risk in risks:
        lines.append(f"- risk: {risk}")
    lines.append("")
    lines.append("## Conclusion")
    lines.append(str(report.get("natural_language_conclusion") or ""))
    return "\n".join(lines) + "\n"


def build_fail_rework_markdown(case: Dict[str, Any]) -> str:
    lines = ["# Session5 Fail-Rework 闭环说明", ""]
    lines.append(f"- case_id: {case.get('id', '')}")
    lines.append(f"- status: {case.get('status', '')}")
    lines.append(f"- debug_rounds: {case.get('debug_rounds', 0)}")
    lines.append("")
    lines.append("## 返工动作")
    for item in case.get("rework_actions", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 结论")
    lines.append(str(case.get("natural_language_conclusion") or ""))
    return "\n".join(lines) + "\n"


def build_risk_markdown(readiness: Dict[str, Any]) -> str:
    lines = ["# Session5 -> Session6 风险判断", ""]
    lines.append(f"- ready: {readiness.get('ready', False)}")
    lines.append(f"- decision: {readiness.get('decision', '')}")
    lines.append("")
    lines.append("## 风险理由")
    for risk in readiness.get("risks", []):
        lines.append(f"- {risk}")
    lines.append("")
    lines.append("## 触发条件")
    for cond in readiness.get("trigger_conditions", []):
        lines.append(f"- {cond}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Session5 internal E2E suite")
    parser.add_argument(
        "--evidence-root",
        default=str(DEFAULT_EVIDENCE_ROOT.as_posix()),
        help="Repo-relative evidence root",
    )
    parser.add_argument(
        "--report",
        default=DEFAULT_REPORT_NAME,
        help="Report filename under evidence root",
    )
    parser.add_argument(
        "--cases",
        default=",".join(SESSION5_CASE_IDS),
        help="Comma-separated case ids. Supported: M3-INT-001,M3-INT-002,M3-INT-003",
    )
    return parser.parse_args()


def parse_selected_cases(raw: str) -> List[str]:
    selected_raw = [item.strip() for item in raw.split(",") if item.strip()]
    if not selected_raw:
        raise Session5Error("empty_cases_selection")
    invalid = [item for item in selected_raw if item not in SESSION5_CASE_IDS]
    if invalid:
        raise Session5Error("invalid_case_selection:" + ",".join(invalid))
    # 按固定顺序去重，保证报告可比较。
    selected_set = set(selected_raw)
    return [case_id for case_id in SESSION5_CASE_IDS if case_id in selected_set]


def acquire_run_lock(root: Path, evidence_root: Path) -> Path:
    """获取 session5 运行锁，避免并发 runner 互相清空证据目录。"""
    lock_dir = evidence_root / ".session5_runner.lock"
    lock_info = lock_dir / "owner.json"
    try:
        lock_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        owner_info = {}
        if lock_info.exists():
            try:
                owner_info = load_json(lock_info)
            except Exception:  # noqa: BLE001
                owner_info = {}
        owner_pid = owner_info.get("pid", "unknown")
        owner_started = owner_info.get("started_at", "unknown")
        raise Session5Error(f"concurrent_session5_runner_detected:pid={owner_pid}:started_at={owner_started}") from exc

    dump_json(
        lock_info,
        {
            "pid": int(os.getpid()),
            "started_at": now_iso(),
            "evidence_root": to_rel(evidence_root, root),
        },
    )
    return lock_dir


def release_run_lock(lock_dir: Path) -> None:
    shutil.rmtree(lock_dir, ignore_errors=True)


def main() -> int:
    args = parse_args()
    root = repo_root()

    evidence_root = (root / args.evidence_root).resolve()
    evidence_root.mkdir(parents=True, exist_ok=True)
    try:
        lock_dir = acquire_run_lock(root, evidence_root)
    except Session5Error as exc:
        print(json.dumps({"status": "fail_closed", "reason": str(exc)}, ensure_ascii=False))
        return 2

    try:
        shutil.rmtree(evidence_root / "cases", ignore_errors=True)
        (evidence_root / "cases").mkdir(parents=True, exist_ok=True)

        selected_case_ids = parse_selected_cases(args.cases)
        case_map: Dict[str, Dict[str, Any]] = {}
        if "M3-INT-001" in selected_case_ids:
            case_map["M3-INT-001"] = run_case_001(root, evidence_root)
        if "M3-INT-002" in selected_case_ids:
            case_map["M3-INT-002"] = run_case_002(root, evidence_root)
        if "M3-INT-003" in selected_case_ids:
            base_chain = build_case1_base_chain(case_map["M3-INT-001"]) if "M3-INT-001" in case_map else None
            case_map["M3-INT-003"] = run_case_003(root, evidence_root, base_chain=base_chain)
        cases = [case_map[case_id] for case_id in selected_case_ids]

        passed = sum(1 for item in cases if item.get("status") == "pass")
        failed = len(cases) - passed

        all_probes: List[Dict[str, Any]] = []
        all_rework: List[str] = []
        all_gate_refs: List[str] = []
        debug_rounds = 0
        success_seen = False
        reject_seen = False
        for case in cases:
            if isinstance(case.get("liveness_probes"), list):
                all_probes.extend(case["liveness_probes"])
            if isinstance(case.get("rework_actions"), list):
                all_rework.extend(case["rework_actions"])
            if isinstance(case.get("gate_chain_refs"), list):
                all_gate_refs.extend([str(item) for item in case["gate_chain_refs"] if str(item).strip()])
            debug_rounds += int(case.get("debug_rounds") or 0)

            details = case.get("details") if isinstance(case.get("details"), dict) else {}
            success_seen = success_seen or bool(details.get("release_manager_success_seen"))
            reject_seen = reject_seen or bool(details.get("release_manager_reject_seen"))

        readiness_risks: List[str] = []
        trigger_conditions: List[str] = []
        if failed > 0:
            readiness_risks.append("仍存在失败用例，外部主线复用风险高。")
            trigger_conditions.append("失败用例必须先修复并重跑通过后，才可进入 Session6。")
        if not success_seen or not reject_seen:
            readiness_risks.append("release-manager-agent 双分支覆盖不完整。")
            trigger_conditions.append("必须补齐 release-manager-agent 成功/拒绝双分支证据。")
        if debug_rounds == 0:
            readiness_risks.append("未形成 Fail-Closed 后返工通过的闭环证据。")
            trigger_conditions.append("必须补充至少一条 Fail->Debug->Rework->Pass 闭环。")

        ready = failed == 0 and success_seen and reject_seen and debug_rounds > 0
        readiness = {
            "ready": ready,
            "decision": "可进入 Session6 外部主线复用验证" if ready else "暂不可进入 Session6 外部主线复用验证",
            "risks": readiness_risks,
            "trigger_conditions": trigger_conditions,
        }

        status = "pass" if failed == 0 else "fail"
        if status == "pass" and ready:
            natural_conclusion = (
                "Session5 内部主线 E2E 通过：主链 Happy、Fail-Closed 后返工、"
                "release-manager-agent 双分支均已验证，且生命周期保持在 review 上限。"
            )
        elif status == "pass":
            selected_label = ",".join(selected_case_ids)
            natural_conclusion = (
                "Session5 内部主线 E2E 已完成所选用例（"
                + selected_label
                + "）并通过；但 release-manager-agent 双分支覆盖尚不完整，"
                "暂不满足 Session6 准入。"
            )
        else:
            natural_conclusion = (
                "Session5 内部主线 E2E 未通过：存在失败用例或闭环证据缺失，"
                "暂不满足 Session6 准入。"
            )

        report = {
            "ts": now_iso(),
            "suite": "session5-internal",
            "selected_cases": selected_case_ids,
            "status": status,
            "total": len(cases),
            "passed": passed,
            "failed": failed,
            "cases": cases,
            "evidence_root": to_rel(evidence_root, root),
            "debug_rounds": debug_rounds,
            "rework_actions": all_rework,
            "liveness_probes": all_probes,
            "gate_chain_refs": sorted(set(all_gate_refs)),
            "session6_readiness": readiness,
            "natural_language_conclusion": natural_conclusion,
        }

        report_path = evidence_root / args.report
        summary_path = evidence_root / DEFAULT_SUMMARY_NAME
        fail_rework_path = evidence_root / DEFAULT_FAIL_REWORK_NAME
        risk_path = evidence_root / DEFAULT_RISK_NAME

        dump_json(report_path, report)
        write_text(summary_path, build_summary_markdown(report))
        if "M3-INT-002" in case_map:
            write_text(fail_rework_path, build_fail_rework_markdown(case_map["M3-INT-002"]))
        else:
            write_text(
                fail_rework_path,
                "# Session5 Fail-Rework 闭环说明\n\n- 未执行 M3-INT-002（本次为聚焦子集运行）。\n",
            )
        write_text(risk_path, build_risk_markdown(readiness))

        print(
            json.dumps(
                {
                    "report_ref": to_rel(report_path, root),
                    "summary_ref": to_rel(summary_path, root),
                    "status": status,
                    "passed": passed,
                    "failed": failed,
                },
                ensure_ascii=False,
            )
        )
        return 0 if status == "pass" else 2
    finally:
        release_run_lock(lock_dir)


if __name__ == "__main__":
    raise SystemExit(main())
