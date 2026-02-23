#!/usr/bin/env python3
"""M1 真实服务语义评审回归入口。

目标：
1. 模拟真实用户提交产品需求，由 QA agent 产出测试设计。
2. 使用 LLM-as-Judge 对 mock 开发交付做语义评审，拒绝字段匹配式“假通过”。
3. 要求 QA 输出缺陷与调试建议，证明其发现问题与 debug 能力。
4. 落盘 BPM 流程实例证据，确保主流程可追溯。
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


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
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate
    return (root / raw).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"json root must be object: {path}")
    return payload


def run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def parse_json_from_mixed_output(text: str) -> Any:
    decoder = json.JSONDecoder()
    fallback: Any = None
    for idx, ch in enumerate(text):
        if ch not in "[{":
            continue
        try:
            value, end = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        remainder = text[idx + end :].strip()
        if not remainder:
            return value
        fallback = value
    if fallback is not None:
        return fallback

    for line in reversed(text.splitlines()):
        raw = line.strip()
        if not raw:
            continue
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            continue
    return {}


def parse_json_text(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    if not text:
        raise RuntimeError("empty agent payload text")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        marker = "```json"
        if marker in text and "```" in text:
            start = text.find(marker) + len(marker)
            end = text.find("```", start)
            if end > start:
                snippet = text[start:end].strip()
                payload = json.loads(snippet)
            else:
                raise RuntimeError("agent payload is not valid json")
        else:
            raise RuntimeError("agent payload is not valid json")
    if not isinstance(payload, dict):
        raise RuntimeError("agent payload json root must be object")
    return payload


def normalize_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        items = [item.strip().strip("'\"") for item in text[1:-1].split(",")]
        return [item for item in items if item]
    return [item.strip() for item in text.split(",") if item.strip()]


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


def write_command_logs(root: Path, case_dir: Path, commands: List[Dict[str, Any]]) -> None:
    lines: List[str] = []
    for item in commands:
        lines.append(f"[{item['step']}] rc={item['return_code']}")
        lines.append(f"cmd: {item['command']}")
        lines.append(f"stdout: {item['stdout_ref']}")
        lines.append(f"stderr: {item['stderr_ref']}")
        lines.append("")
    command_log = case_dir / "commands.txt"
    command_log.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    dump_json(case_dir / "command_trace.json", {"commands": commands, "generated_at": now_iso()})


def parse_qa_agent_response(proc: subprocess.CompletedProcess[str]) -> Tuple[Dict[str, Any], str, Dict[str, Any]]:
    outer_payload = parse_json_from_mixed_output(proc.stdout)
    if not isinstance(outer_payload, dict):
        raise RuntimeError("qa agent output missing outer json payload")

    result = outer_payload.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("qa agent output missing result")
    payloads = result.get("payloads")
    if not isinstance(payloads, list) or not payloads:
        raise RuntimeError("qa agent output missing payloads")
    first = payloads[0]
    if not isinstance(first, dict):
        raise RuntimeError("qa agent output payload item invalid")

    text = str(first.get("text") or "").strip()
    if not text:
        raise RuntimeError("qa agent payload text is empty")

    inner_payload = parse_json_text(text)
    return outer_payload, text, inner_payload


def build_service_test_doc(*, objective: str, expected_conditions: List[str]) -> str:
    lines = [
        "# m1-real-service-semantic - Test Cases",
        "",
        "## Objective Alignment",
        "",
        "验证真实用户服务场景下，QA 能对 mock 交付执行语义评审并发现关键问题。",
        "",
        "## Test Cases",
        "",
        "### TC-001: 产品需求交付语义校验",
        "",
        "- Type: Objective",
        "- Priority: P0",
        "- Input: mock 开发交付结果",
        "- Expected: 能识别关键能力缺失并拒绝放行",
        "- Evaluation Method: LLM-Judge",
        "- Judge Payload:",
        f"  - objective: {objective}",
        f"  - expected_conditions: [{', '.join(expected_conditions)}]",
        "  - reference_response: 输出必须覆盖核心需求功能、异常处理策略与测试证据，否则视为未完成交付",
        "  - grader_selection: [relevance, correctness]",
        "",
        "## Evaluation Configuration",
        "",
        "- Objective Eval Rounds: 1",
        "- Subjective Eval Rounds: 0",
        "- Judge Perspectives: [qa]",
        "- Timeout Seconds: 600",
        "- Retry Policy: max 1",
        "",
    ]
    return "\n".join(lines)


def build_markdown_summary(summary: Dict[str, Any]) -> str:
    lines = [
        "# Runtime Validation Round 8 - Semantic Service Summary",
        "",
        f"- 生成时间: `{summary['ts']}`",
        f"- 总体状态: `{summary['status']}`",
        f"- gate_decision: `{summary['gate_decision']}`",
        f"- qa_findings_count: `{summary['qa_findings_count']}`",
        f"- qa_debug_steps_count: `{summary['qa_debug_steps_count']}`",
        "",
        "## 关键证据",
        "",
        f"- `service_request_ref`: `{summary['critical_refs']['service_request_ref']}`",
        f"- `process_instance_start_ref`: `{summary['critical_refs']['process_instance_start_ref']}`",
        f"- `qa_design_ref`: `{summary['critical_refs']['qa_design_ref']}`",
        f"- `test_doc_ref`: `{summary['critical_refs']['test_doc_ref']}`",
        f"- `preparation_output_ref`: `{summary['critical_refs']['preparation_output_ref']}`",
        f"- `evaluation_output_ref`: `{summary['critical_refs']['evaluation_output_ref']}`",
        f"- `raw_eval_ref`: `{summary['critical_refs']['raw_eval_ref']}`",
        f"- `qa_execution_report_ref`: `{summary['critical_refs']['qa_execution_report_ref']}`",
        "",
        "## 自然语言结论",
        "",
        summary["natural_language_conclusion"],
        "",
    ]
    if summary.get("risks"):
        lines.extend(["## 风险敞口", ""])
        for item in summary["risks"]:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run M1 semantic service validation")
    parser.add_argument(
        "--evidence-root",
        default="docs/design/modules/evidence/quality-gate/runtime-validation-round-8-semantic-service",
        help="Repo-relative evidence root",
    )
    parser.add_argument(
        "--judge-model",
        default="gpt-5.3-codex",
        help="Judge model for quality_eval_runner",
    )
    parser.add_argument(
        "--profile-set",
        default="quality-gate.baseline@1.0.0",
        help="Comma-separated profile set",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    evidence_root = resolve_path(root, args.evidence_root)
    case_dir = evidence_root / "TC-M1-SERVICE-001"
    summary_json = evidence_root / "runtime_summary.json"
    summary_md = evidence_root / "runtime_summary.md"

    if evidence_root.exists():
        shutil.rmtree(evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)

    commands: List[Dict[str, Any]] = []
    risks: List[str] = []

    service_request_path = case_dir / "service_request.md"
    mock_delivery_path = case_dir / "mock_delivery_output.md"
    qa_design_request_path = case_dir / "qa_design_request.txt"
    qa_design_json_path = case_dir / "qa_design_payload.json"
    qa_design_text_path = case_dir / "qa_design_payload.txt"
    qa_test_plan_md = case_dir / "qa_test_plan.md"
    test_doc_path = case_dir / "TEST_service_llm.md"
    prep_input_path = case_dir / "prep_input.json"
    prep_output_path = case_dir / "prep_output.json"
    eval_output_dir = case_dir / "evaluation"
    qa_execution_request_path = case_dir / "qa_execution_request.txt"
    qa_execution_json_path = case_dir / "qa_execution_report.json"
    qa_execution_text_path = case_dir / "qa_execution_report.txt"
    process_start_output_path = case_dir / "process_instance_start.json"
    process_validate_output_path = case_dir / "process_instance_validate.json"
    process_replay_output_path = case_dir / "process_instance_replay.json"
    instance_root = case_dir / "instances"

    service_request = """# 产品需求（真实服务模拟）

## 背景
HR 需要上线一个“员工请假审批”能力，覆盖提交、审批、审计和风控，作为公司内网系统的首批上线功能。

## 目标
1. 员工可提交请假申请（开始/结束时间、原因、附件）。
2. 直属主管可审批（通过/拒绝）并附理由。
3. 系统必须记录审计日志（提交、审批、状态变化）。
4. 必须有基础权限控制（员工仅可看本人申请，主管仅可看本团队申请）。
5. 必须有接口级限流（避免刷接口）。
6. 必须有最小可执行测试证据（至少包含关键路径与异常路径）。

## 验收口径
若交付结果缺失任一核心能力（权限、审计、限流、关键测试证据），判定为不通过，禁止进入发布门禁。
"""
    service_request_path.write_text(service_request, encoding="utf-8")

    # mock 交付刻意保留关键缺失，用于验证 QA 能发现问题并给出 debug 建议。
    mock_delivery = """# 开发交付说明（Mock）

本次仅完成：
1. README 文档补充。
2. 提交了占位 API 路由，未实现真实业务逻辑。

未完成项：
1. 权限控制（RBAC）后续再做。
2. 审计日志后续再做。
3. 限流策略后续再做。
4. 自动化测试后续再做。
"""
    mock_delivery_path.write_text(mock_delivery, encoding="utf-8")

    # 步骤 1：创建 BPM 实例（主流程接点），并校验实例契约可回放。
    process_start_cmd = [
        sys.executable,
        "skills/system/process-instance-manager/scripts/process_instance_runner.py",
        "start",
        "--process-id",
        "development-process",
        "--phase-id",
        "p2",
        "--instance-root",
        to_rel(instance_root, root),
        "--instance-id",
        "tc-m1-service-001",
        "--objective-ref",
        "obj-m1-real-service-semantic-validation",
        "--initiated-by",
        "hr",
        "--input-ref",
        to_rel(service_request_path, root),
        "--output",
        to_rel(process_start_output_path, root),
    ]
    process_start_proc = exec_step(
        root=root,
        case_dir=case_dir,
        step="process_start",
        cmd=process_start_cmd,
        commands=commands,
    )
    if process_start_proc.returncode != 0 or not process_start_output_path.exists():
        risks.append("process instance start failed")

    process_validate_cmd = [
        sys.executable,
        "skills/system/process-instance-manager/scripts/process_instance_runner.py",
        "validate",
        "--instance-root",
        to_rel(instance_root, root),
        "--output",
        to_rel(process_validate_output_path, root),
    ]
    process_validate_proc = exec_step(
        root=root,
        case_dir=case_dir,
        step="process_validate",
        cmd=process_validate_cmd,
        commands=commands,
    )
    if process_validate_proc.returncode != 0:
        risks.append("process instance validate failed")

    process_replay_cmd = [
        sys.executable,
        "skills/system/process-instance-manager/scripts/process_instance_runner.py",
        "replay",
        "--instance-root",
        to_rel(instance_root, root),
        "--output",
        to_rel(process_replay_output_path, root),
    ]
    process_replay_proc = exec_step(
        root=root,
        case_dir=case_dir,
        step="process_replay",
        cmd=process_replay_cmd,
        commands=commands,
    )
    if process_replay_proc.returncode != 0:
        risks.append("process instance replay failed")

    session_id = ""
    if process_start_output_path.exists():
        process_start_payload = load_json(process_start_output_path)
        binding_ref = str(process_start_payload.get("session_binding_ref") or "")
        if binding_ref:
            binding_path = resolve_path(root, binding_ref)
            if binding_path.exists():
                binding_payload = load_json(binding_path)
                session_id = str(binding_payload.get("session_id") or "")
    if not session_id:
        risks.append("missing qa session id from process instance")

    # 步骤 2：通过 QA agent 生成测试设计（真实服务目标驱动）。
    qa_design_request = f"""你现在是 QA Agent，请基于以下产品需求输出严格 JSON（禁止额外文本）：
{{
  "objective": "一句话测试目标",
  "expected_conditions": ["至少5条，可用于LLM-Judge expected_conditions"],
  "risk_focus": ["P0","P1"],
  "test_plan_markdown": "Markdown格式测试计划，必须包含关键路径、异常路径、失败判定",
  "mock_signals": ["你识别到的mock交付信号"]
}}

需求如下：
{service_request}
"""
    qa_design_request_path.write_text(qa_design_request, encoding="utf-8")
    qa_design_cmd = [
        "openclaw",
        "agent",
        "--agent",
        "qa",
        "--session-id",
        session_id or "tc-m1-service-001-fallback",
        "--message",
        qa_design_request,
        "--json",
    ]
    qa_design_proc = exec_step(
        root=root,
        case_dir=case_dir,
        step="qa_design",
        cmd=qa_design_cmd,
        commands=commands,
    )

    qa_design_payload: Dict[str, Any] = {}
    if qa_design_proc.returncode == 0:
        try:
            _, qa_design_text, qa_design_payload = parse_qa_agent_response(qa_design_proc)
            qa_design_text_path.write_text(qa_design_text + "\n", encoding="utf-8")
            dump_json(qa_design_json_path, qa_design_payload)
        except Exception as exc:
            risks.append(f"qa design parse failed: {exc}")
    else:
        risks.append("qa design call failed")

    expected_conditions = normalize_string_list(qa_design_payload.get("expected_conditions"))
    if len(expected_conditions) < 5:
        expected_conditions = [
            "请假申请创建接口",
            "主管审批接口",
            "RBAC 权限控制",
            "审计日志链路",
            "接口限流策略",
            "关键路径与异常路径测试证据",
        ]
        risks.append("qa expected_conditions fallback to default")

    objective = str(qa_design_payload.get("objective") or "").strip() or "验证交付是否真正实现请假审批核心能力"
    qa_plan_md = str(qa_design_payload.get("test_plan_markdown") or "").strip()
    if qa_plan_md:
        qa_test_plan_md.write_text(qa_plan_md + "\n", encoding="utf-8")
    else:
        qa_test_plan_md.write_text("QA 未返回可解析 test_plan_markdown，已使用默认评测契约。\n", encoding="utf-8")
        risks.append("qa test plan markdown missing")

    test_doc_path.write_text(
        build_service_test_doc(objective=objective, expected_conditions=expected_conditions),
        encoding="utf-8",
    )

    # 步骤 3：M1 preparation，编译 QA 测试设计。
    prep_input_payload = {
        "objective_ref": "obj-m1-real-service-semantic-validation",
        "spec_ref": "docs/design/modules/M1-test-system.md",
        "test_doc_ref": to_rel(test_doc_path, root),
        "risk_focus": normalize_string_list(qa_design_payload.get("risk_focus")) or ["P0", "P1"],
    }
    dump_json(prep_input_path, prep_input_payload)

    prep_cmd = [
        sys.executable,
        "processes/meta/quality-gate-preparation/scripts/quality_gate_preparation_runner.py",
        "--input",
        to_rel(prep_input_path, root),
        "--output",
        to_rel(prep_output_path, root),
        "--evidence-dir",
        to_rel(case_dir / "preparation", root),
        "--run-id",
        "TC-M1-SERVICE-001-prep",
        "--profile-set",
        args.profile_set,
    ]
    prep_proc = exec_step(
        root=root,
        case_dir=case_dir,
        step="preparation",
        cmd=prep_cmd,
        commands=commands,
    )

    preparation_bundle_ref = ""
    prep_verdict = ""
    if prep_proc.returncode == 0 and prep_output_path.exists():
        prep_output_payload = load_json(prep_output_path)
        prep_verdict = str(prep_output_payload.get("verdict") or "")
        preparation_bundle_ref = str(prep_output_payload.get("preparation_bundle_ref") or "")
        if prep_verdict != "pass" or not preparation_bundle_ref:
            risks.append("preparation verdict is not pass")
    else:
        risks.append("preparation runner failed")

    # 步骤 4：LLM-as-Judge 语义评测 mock 交付。
    eval_payload: Dict[str, Any] = {}
    raw_eval_ref = ""
    gate_decision = "unknown"
    if preparation_bundle_ref:
        eval_cmd = [
            "skills/system/qa/evaluation-runner/scripts/quality_eval_runner",
            "run",
            "--preparation-bundle",
            preparation_bundle_ref,
            "--mode",
            "objective",
            "--actual-output",
            to_rel(mock_delivery_path, root),
            "--judge-model",
            args.judge_model,
            "--module",
            "M1",
            "--output-dir",
            to_rel(eval_output_dir, root),
        ]
        eval_proc = exec_step(
            root=root,
            case_dir=case_dir,
            step="semantic_eval",
            cmd=eval_cmd,
            commands=commands,
        )
        parsed_eval = parse_json_from_mixed_output(eval_proc.stdout)
        if isinstance(parsed_eval, dict):
            eval_payload = parsed_eval
            gate_decision = str(parsed_eval.get("gate_decision") or "unknown")
            raw_eval_ref = str(parsed_eval.get("raw_eval_ref") or "")
        else:
            risks.append("semantic eval stdout parse failed")
    else:
        risks.append("semantic eval skipped due missing preparation bundle")

    llm_judge_used = False
    semantic_detection_ok = False
    if raw_eval_ref:
        raw_eval_path = resolve_path(root, raw_eval_ref)
        if raw_eval_path.exists():
            raw_eval_payload = load_json(raw_eval_path)
            run_payload = raw_eval_payload.get("run")
            if isinstance(run_payload, dict):
                case_results = run_payload.get("case_results")
                if isinstance(case_results, list) and case_results:
                    first = case_results[0]
                    if isinstance(first, dict):
                        llm_judge_used = str(first.get("evaluation_method") or "") == "LLM-Judge"
                        semantic_detection_ok = str(first.get("decision") or "") in {"fail", "hold"}
    if not llm_judge_used:
        risks.append("llm judge method was not used")
    if gate_decision not in {"fail", "hold"}:
        risks.append(f"gate_decision not blocking mock output: {gate_decision}")
    if not semantic_detection_ok:
        risks.append("semantic detection did not flag mock output")

    # 步骤 5：QA agent 基于评测结果输出缺陷与 debug 建议。
    qa_execution_report: Dict[str, Any] = {}
    if raw_eval_ref:
        qa_execution_request = f"""你是 QA Agent。已完成一次真实服务评测，请基于以下信息输出严格 JSON（禁止额外文本）：
{{
  "gate_decision_recommendation": "fail|hold|pass",
  "findings": [
    {{
      "id": "F-*",
      "severity": "P0|P1|P2",
      "title": "简短标题",
      "evidence": "引用哪条评测证据",
      "repro_steps": ["复现步骤"],
      "debug_steps": ["调试步骤"]
    }}
  ],
  "debug_plan": ["总体调试计划"],
  "conclusion": "结论"
}}

产品需求：
{service_request}

Mock 开发交付：
{mock_delivery}

语义评测输出引用：
- raw_eval_ref: {raw_eval_ref}
- gate_decision: {gate_decision}
"""
        qa_execution_request_path.write_text(qa_execution_request, encoding="utf-8")
        qa_exec_cmd = [
            "openclaw",
            "agent",
            "--agent",
            "qa",
            "--session-id",
            session_id or "tc-m1-service-001-fallback",
            "--message",
            qa_execution_request,
            "--json",
        ]
        qa_exec_proc = exec_step(
            root=root,
            case_dir=case_dir,
            step="qa_execution",
            cmd=qa_exec_cmd,
            commands=commands,
        )
        if qa_exec_proc.returncode == 0:
            try:
                _, qa_execution_text, qa_execution_report = parse_qa_agent_response(qa_exec_proc)
                qa_execution_text_path.write_text(qa_execution_text + "\n", encoding="utf-8")
                dump_json(qa_execution_json_path, qa_execution_report)
            except Exception as exc:
                risks.append(f"qa execution parse failed: {exc}")
        else:
            risks.append("qa execution call failed")
    else:
        risks.append("qa execution skipped due missing raw_eval_ref")

    findings = qa_execution_report.get("findings")
    debug_plan = qa_execution_report.get("debug_plan")
    qa_findings_count = len(findings) if isinstance(findings, list) else 0
    qa_debug_steps_count = len(debug_plan) if isinstance(debug_plan, list) else 0

    if qa_findings_count == 0:
        risks.append("qa findings are empty")
    if qa_debug_steps_count == 0:
        risks.append("qa debug plan is empty")

    status = "pass" if not risks else "fail"
    natural_language_conclusion = (
        "已完成真实服务场景验证：QA agent 先产出测试设计，再对 mock 交付进行 LLM 语义评审，门禁阻断并输出可执行 debug 建议。"
        if status == "pass"
        else "本轮未满足真实服务语义评审闭环门禁，存在关键敞口，请先修复风险后再宣告通过。"
    )

    write_command_logs(root, case_dir, commands)

    summary = {
        "ts": now_iso(),
        "suite": "TC-M1-SERVICE-001",
        "status": status,
        "gate_decision": gate_decision,
        "qa_findings_count": qa_findings_count,
        "qa_debug_steps_count": qa_debug_steps_count,
        "llm_judge_used": llm_judge_used,
        "semantic_detection_ok": semantic_detection_ok,
        "critical_refs": {
            "service_request_ref": to_rel(service_request_path, root),
            "process_instance_start_ref": to_rel(process_start_output_path, root),
            "process_instance_validate_ref": to_rel(process_validate_output_path, root),
            "process_instance_replay_ref": to_rel(process_replay_output_path, root),
            "qa_design_ref": to_rel(qa_design_json_path, root),
            "test_doc_ref": to_rel(test_doc_path, root),
            "preparation_output_ref": to_rel(prep_output_path, root),
            "evaluation_output_ref": to_rel(eval_output_dir / "raw_eval.json", root) if (eval_output_dir / "raw_eval.json").exists() else "",
            "raw_eval_ref": raw_eval_ref,
            "qa_execution_report_ref": to_rel(qa_execution_json_path, root),
            "command_trace_ref": to_rel(case_dir / "command_trace.json", root),
        },
        "risks": risks,
        "natural_language_conclusion": natural_language_conclusion,
    }
    dump_json(summary_json, summary)
    summary_md.write_text(build_markdown_summary(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
