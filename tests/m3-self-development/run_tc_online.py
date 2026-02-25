#!/usr/bin/env python3
"""M3 自开发在线测试统一入口（Session4/Session5）。

设计原则：
1. 单 runner + --suite/--case 选择执行范围。
2. 复用上游 runner（M3 runtime / M1 runtime），不重复实现评测引擎。
3. Session6 预留 case 仅注册不执行；若强制执行则 Fail-Closed。
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


DEFAULT_EVIDENCE_ROOT = Path("tmp/runtime_data/execution/evidence/self-development/e2e-online/session4-foundation/latest")
DEFAULT_REPORT_NAME = "session4_tc_online_report.json"
DEFAULT_MARKDOWN_NAME = "session4_tc_online_summary.md"

SESSION4_COVERAGE_CLASSES = ("happy", "exception", "fail-closed", "rollback")


@dataclass(frozen=True)
class CaseDef:
    case_id: str
    suite: str
    category: str
    status: str
    description: str
    upstream: str
    session: str


CASES: List[CaseDef] = [
    CaseDef(
        case_id="M3-S4-HAPPY-001",
        suite="session4-happy",
        category="happy",
        status="executable",
        description="验证 M3 runtime 主链路 happy path 作为 Session5/6 基座。",
        upstream="m3-runtime",
        session="session4",
    ),
    CaseDef(
        case_id="M3-S4-EXC-001",
        suite="session4-exception",
        category="exception",
        status="executable",
        description="验证 M1 gate 决策中的 hold 路由（异常链路）可达。",
        upstream="m1-runtime",
        session="session4",
    ),
    CaseDef(
        case_id="M3-S4-FC-001",
        suite="session4-fail-closed",
        category="fail-closed",
        status="executable",
        description="验证关键输入异常时 M1 fail-closed 判定有效。",
        upstream="m1-runtime",
        session="session4",
    ),
    CaseDef(
        case_id="M3-S4-RW-001",
        suite="session4-rollback",
        category="rollback",
        status="executable",
        description="验证 release-manager 回退/返工分支（rejected/blocked）有效。",
        upstream="m3-runtime",
        session="session4",
    ),
    CaseDef(
        case_id="M3-INT-001",
        suite="session5-internal",
        category="internal",
        status="executable",
        description="Session5 内部主线 E2E 场景 1（主链 Happy）。",
        upstream="session5-runtime",
        session="session5",
    ),
    CaseDef(
        case_id="M3-INT-002",
        suite="session5-internal",
        category="internal",
        status="executable",
        description="Session5 内部主线 E2E 场景 2（Fail-Closed -> Debug -> 修复 -> 重跑）。",
        upstream="session5-runtime",
        session="session5",
    ),
    CaseDef(
        case_id="M3-INT-003",
        suite="session5-internal",
        category="internal",
        status="executable",
        description="Session5 内部主线 E2E 场景 3（release-manager-agent 双分支）。",
        upstream="session5-runtime",
        session="session5",
    ),
    CaseDef(
        case_id="M3-EXT-001",
        suite="session6-external",
        category="external",
        status="reserved",
        description="Session6 外部主线 E2E 场景 1（预留）。",
        upstream="reserved",
        session="session6",
    ),
    CaseDef(
        case_id="M3-EXT-002",
        suite="session6-external",
        category="external",
        status="reserved",
        description="Session6 外部主线 E2E 场景 2（预留）。",
        upstream="reserved",
        session="session6",
    ),
    CaseDef(
        case_id="M3-EXT-003",
        suite="session6-external",
        category="external",
        status="reserved",
        description="Session6 外部主线 E2E 场景 3（预留）。",
        upstream="reserved",
        session="session6",
    ),
    CaseDef(
        case_id="M3-FC-101",
        suite="session6-external",
        category="cross-fc",
        status="reserved",
        description="跨主线 Fail-Closed/旁路阻断场景 101（预留）。",
        upstream="reserved",
        session="session6",
    ),
    CaseDef(
        case_id="M3-FC-102",
        suite="session6-external",
        category="cross-fc",
        status="reserved",
        description="跨主线 Fail-Closed/旁路阻断场景 102（预留）。",
        upstream="reserved",
        session="session6",
    ),
    CaseDef(
        case_id="M3-FC-103",
        suite="session6-external",
        category="cross-fc",
        status="reserved",
        description="跨主线 Fail-Closed/旁路阻断场景 103（预留）。",
        upstream="reserved",
        session="session6",
    ),
]

CASE_BY_ID: Dict[str, CaseDef] = {item.case_id: item for item in CASES}
SUITE_TO_CASES: Dict[str, List[str]] = {
    "session4-happy": ["M3-S4-HAPPY-001"],
    "session4-exception": ["M3-S4-EXC-001"],
    "session4-fail-closed": ["M3-S4-FC-001"],
    "session4-rollback": ["M3-S4-RW-001"],
    "session5-internal": ["M3-INT-001", "M3-INT-002", "M3-INT-003"],
    "session6-external": ["M3-EXT-001", "M3-EXT-002", "M3-EXT-003", "M3-FC-101", "M3-FC-102", "M3-FC-103"],
}
DEFAULT_SESSION4_CASES: List[str] = [
    "M3-S4-HAPPY-001",
    "M3-S4-EXC-001",
    "M3-S4-FC-001",
    "M3-S4-RW-001",
]
SUITE_TO_CASES["all"] = [item.case_id for item in CASES]


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


def split_csv(raw: str) -> List[str]:
    values = [item.strip() for item in raw.split(",")]
    return [item for item in values if item]


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
        raise RuntimeError(f"json root must be object: {path}")
    return payload


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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Session4 M3 self-development online suites")
    parser.add_argument(
        "--suite",
        default="",
        help="Comma-separated suites: session4-happy,session4-exception,session4-fail-closed,session4-rollback,session5-internal,session6-external,all",
    )
    parser.add_argument(
        "--case",
        default="",
        help="Comma-separated case ids",
    )
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
        "--list-cases",
        action="store_true",
        help="List supported cases and exit",
    )
    return parser.parse_args()


def materialize_selection(args: argparse.Namespace) -> Dict[str, Any]:
    suite_inputs = split_csv(args.suite)
    case_inputs = split_csv(args.case)
    errors: List[str] = []
    selected: Set[str] = set()

    for suite_name in suite_inputs:
        if suite_name not in SUITE_TO_CASES:
            errors.append(f"unknown_suite:{suite_name}")
            continue
        selected.update(SUITE_TO_CASES[suite_name])

    for case_id in case_inputs:
        if case_id not in CASE_BY_ID:
            errors.append(f"unknown_case:{case_id}")
            continue
        selected.add(case_id)

    default_mode = not suite_inputs and not case_inputs
    if default_mode:
        selected = set(DEFAULT_SESSION4_CASES)

    ordered = [item.case_id for item in CASES if item.case_id in selected]
    return {
        "suite_inputs": suite_inputs,
        "case_inputs": case_inputs,
        "default_mode": default_mode,
        "selected_case_ids": ordered,
        "errors": errors,
    }


def write_command_evidence(
    *,
    root: Path,
    cmd_dir: Path,
    command_id: str,
    cmd: List[str],
    proc: subprocess.CompletedProcess[str],
) -> Dict[str, Any]:
    stdout_path = cmd_dir / f"{command_id}.stdout.txt"
    stderr_path = cmd_dir / f"{command_id}.stderr.txt"
    command_path = cmd_dir / f"{command_id}.command.txt"
    write_text(stdout_path, proc.stdout)
    write_text(stderr_path, proc.stderr)
    write_text(command_path, " ".join(cmd) + "\n")
    return {
        "command_id": command_id,
        "command": " ".join(cmd),
        "return_code": proc.returncode,
        "stdout_ref": to_rel(stdout_path, root),
        "stderr_ref": to_rel(stderr_path, root),
        "command_ref": to_rel(command_path, root),
    }


def run_upstream_m3(root: Path, evidence_root: Path) -> Dict[str, Any]:
    upstream_root = evidence_root / "upstream" / "m3-runtime"
    upstream_root.mkdir(parents=True, exist_ok=True)
    cmd = [
        "python3",
        "tests/m3-runtime/run_skill_contract_validation.py",
        "--evidence-root",
        to_rel(upstream_root, root),
        "--report",
        "skill_contract_validation_report.json",
    ]
    proc = run_cmd(cmd, root)
    command_trace = write_command_evidence(root=root, cmd_dir=upstream_root, command_id="run_m3_runtime", cmd=cmd, proc=proc)
    summary = parse_json_from_mixed_output(proc.stdout)
    summary_obj = summary if isinstance(summary, dict) else {}
    report_ref_raw = str(summary_obj.get("report_ref") or "")
    report_path = (root / report_ref_raw).resolve() if report_ref_raw else (upstream_root / "skill_contract_validation_report.json").resolve()
    report_exists = report_path.exists()
    report_payload = load_json(report_path) if report_exists else {}
    return {
        "status": "ok" if (proc.returncode == 0 and report_exists) else "failed",
        "return_code": proc.returncode,
        "summary": summary_obj,
        "report_ref": to_rel(report_path, root) if report_exists else "",
        "report_payload": report_payload,
        "command_trace": command_trace,
    }


def run_upstream_m1(root: Path, evidence_root: Path) -> Dict[str, Any]:
    upstream_root = evidence_root / "upstream" / "m1-runtime"
    upstream_root.mkdir(parents=True, exist_ok=True)
    report_rel = to_rel(upstream_root / "latest_post_dev_regression_summary.json", root)
    markdown_rel = to_rel(upstream_root / "latest_post_dev_regression_summary.md", root)
    cmd = [
        "python3",
        "tests/m1-runtime/run_post_dev_regression.py",
        "--evidence-root",
        to_rel(upstream_root, root),
        "--report",
        report_rel,
        "--markdown-report",
        markdown_rel,
    ]
    proc = run_cmd(cmd, root)
    command_trace = write_command_evidence(root=root, cmd_dir=upstream_root, command_id="run_m1_runtime", cmd=cmd, proc=proc)
    summary = parse_json_from_mixed_output(proc.stdout)
    summary_obj = summary if isinstance(summary, dict) else {}
    report_path = (upstream_root / "latest_post_dev_regression_summary.json").resolve()
    report_exists = report_path.exists()
    report_payload = load_json(report_path) if report_exists else {}
    return {
        "status": "ok" if (proc.returncode == 0 and report_exists) else "failed",
        "return_code": proc.returncode,
        "summary": summary_obj,
        "report_ref": to_rel(report_path, root) if report_exists else "",
        "report_payload": report_payload,
        "command_trace": command_trace,
    }


def run_upstream_session5(root: Path) -> Dict[str, Any]:
    """运行 Session5 内部主线执行器（证据固定落在 tmp 路径）。"""
    evidence_root = (
        root
        / "tmp/runtime_data/execution/evidence/construction-plane/"
        "R-20260222-M6-m3-self-development-e2e-online-01/session5"
    ).resolve()
    evidence_root.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python3",
        "tests/m3-self-development/session5_internal_runner.py",
        "--evidence-root",
        to_rel(evidence_root, root),
        "--report",
        "session5_report.json",
    ]
    proc = run_cmd(cmd, root)
    command_trace = write_command_evidence(
        root=root,
        cmd_dir=evidence_root,
        command_id="run_session5_internal",
        cmd=cmd,
        proc=proc,
    )
    summary = parse_json_from_mixed_output(proc.stdout)
    summary_obj = summary if isinstance(summary, dict) else {}
    report_ref_raw = str(summary_obj.get("report_ref") or "")
    report_path = (root / report_ref_raw).resolve() if report_ref_raw else (evidence_root / "session5_report.json").resolve()
    report_exists = report_path.exists()
    report_payload = load_json(report_path) if report_exists else {}
    return {
        "status": "ok" if (proc.returncode == 0 and report_exists) else "failed",
        "return_code": proc.returncode,
        "summary": summary_obj,
        "report_ref": to_rel(report_path, root) if report_exists else "",
        "report_payload": report_payload,
        "command_trace": command_trace,
    }


def case_status_map(payload: Dict[str, Any]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for item in payload.get("cases", []):
        if isinstance(item, dict):
            case_id = item.get("id")
            status = item.get("status")
            if isinstance(case_id, str) and isinstance(status, str):
                result[case_id] = status
    return result


def assert_true(assertions: List[Dict[str, Any]], name: str, condition: bool, details: str) -> bool:
    assertions.append(
        {
            "name": name,
            "passed": bool(condition),
            "details": details,
        }
    )
    return bool(condition)


def evaluate_case(case_def: CaseDef, upstream_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    assertions: List[Dict[str, Any]] = []
    passed = True
    notes: List[str] = []
    upstream_refs: Dict[str, str] = {}

    if case_def.case_id == "M3-S4-HAPPY-001":
        upstream = upstream_results["m3-runtime"]
        upstream_refs["m3_report_ref"] = upstream.get("report_ref", "")
        report_payload = upstream.get("report_payload", {})
        status_map = case_status_map(report_payload if isinstance(report_payload, dict) else {})
        passed &= assert_true(assertions, "upstream_m3_return_code", upstream.get("return_code") == 0, "m3-runtime runner 返回码必须为 0。")
        passed &= assert_true(assertions, "tc_impact_happy_pass", status_map.get("TC-IMPACT-HP") == "pass", "TC-IMPACT-HP 必须通过。")
        passed &= assert_true(assertions, "tc_release_happy_pass", status_map.get("TC-RELEASE-HP") == "pass", "TC-RELEASE-HP 必须通过。")
    elif case_def.case_id == "M3-S4-EXC-001":
        upstream = upstream_results["m1-runtime"]
        upstream_refs["m1_report_ref"] = upstream.get("report_ref", "")
        report_payload = upstream.get("report_payload", {})
        status_map = case_status_map(report_payload if isinstance(report_payload, dict) else {})
        decision_coverage = report_payload.get("decision_coverage", {}) if isinstance(report_payload, dict) else {}
        passed &= assert_true(assertions, "upstream_m1_return_code", upstream.get("return_code") == 0, "m1-runtime runner 返回码必须为 0。")
        passed &= assert_true(assertions, "hold_coverage", bool(decision_coverage.get("hold")), "decision_coverage.hold 必须为 true。")
        passed &= assert_true(assertions, "tc_m1_hold_pass", status_map.get("TC-M1-CHAIN-003") == "pass", "TC-M1-CHAIN-003 必须通过。")
    elif case_def.case_id == "M3-S4-FC-001":
        upstream = upstream_results["m1-runtime"]
        upstream_refs["m1_report_ref"] = upstream.get("report_ref", "")
        report_payload = upstream.get("report_payload", {})
        status_map = case_status_map(report_payload if isinstance(report_payload, dict) else {})
        decision_coverage = report_payload.get("decision_coverage", {}) if isinstance(report_payload, dict) else {}
        passed &= assert_true(assertions, "upstream_m1_return_code", upstream.get("return_code") == 0, "m1-runtime runner 返回码必须为 0。")
        passed &= assert_true(assertions, "fail_closed_coverage", bool(decision_coverage.get("fail_closed")), "decision_coverage.fail_closed 必须为 true。")
        passed &= assert_true(assertions, "tc_m1_fail_closed_pass", status_map.get("TC-M1-CHAIN-002") == "pass", "TC-M1-CHAIN-002 必须通过。")
    elif case_def.case_id == "M3-S4-RW-001":
        upstream = upstream_results["m3-runtime"]
        upstream_refs["m3_report_ref"] = upstream.get("report_ref", "")
        report_payload = upstream.get("report_payload", {})
        status_map = case_status_map(report_payload if isinstance(report_payload, dict) else {})
        passed &= assert_true(assertions, "upstream_m3_return_code", upstream.get("return_code") == 0, "m3-runtime runner 返回码必须为 0。")
        passed &= assert_true(
            assertions,
            "tc_release_fail_closed_reg_pass",
            status_map.get("TC-RELEASE-FC-REG") == "pass",
            "TC-RELEASE-FC-REG 必须通过以证明返工阻断链路。",
        )
        passed &= assert_true(
            assertions,
            "tc_release_fail_closed_rb_pass",
            status_map.get("TC-RELEASE-FC-RB") == "pass",
            "TC-RELEASE-FC-RB 必须通过以证明回退包缺失阻断链路。",
        )
    elif case_def.case_id in {"M3-INT-001", "M3-INT-002", "M3-INT-003"}:
        upstream = upstream_results["session5-runtime"]
        upstream_refs["session5_report_ref"] = upstream.get("report_ref", "")
        report_payload = upstream.get("report_payload", {})
        cases_raw = report_payload.get("cases", []) if isinstance(report_payload, dict) else []
        case_map: Dict[str, Dict[str, Any]] = {}
        for item in cases_raw:
            if isinstance(item, dict):
                cid = item.get("id")
                if isinstance(cid, str):
                    case_map[cid] = item

        case_payload = case_map.get(case_def.case_id, {})
        case_status = str(case_payload.get("status") or "")
        passed &= assert_true(assertions, "upstream_session5_return_code", upstream.get("return_code") == 0, "session5 runner 返回码必须为 0。")
        passed &= assert_true(assertions, "session5_case_pass", case_status == "pass", f"{case_def.case_id} 必须为 pass。")

        if case_def.case_id == "M3-INT-001":
            gate_refs = case_payload.get("gate_chain_refs") if isinstance(case_payload.get("gate_chain_refs"), list) else []
            passed &= assert_true(assertions, "gate_chain_refs_present", bool(gate_refs), "M3-INT-001 必须包含门禁链路引用。")
        elif case_def.case_id == "M3-INT-002":
            debug_rounds = int(case_payload.get("debug_rounds") or 0)
            rework_actions = case_payload.get("rework_actions") if isinstance(case_payload.get("rework_actions"), list) else []
            passed &= assert_true(assertions, "debug_rounds_ge_1", debug_rounds >= 1, "M3-INT-002 必须至少包含一轮 debug。")
            passed &= assert_true(assertions, "rework_actions_present", bool(rework_actions), "M3-INT-002 必须落盘返工动作。")
        elif case_def.case_id == "M3-INT-003":
            details = case_payload.get("details") if isinstance(case_payload.get("details"), dict) else {}
            success_seen = bool(details.get("release_manager_success_seen"))
            reject_seen = bool(details.get("release_manager_reject_seen"))
            passed &= assert_true(assertions, "release_manager_success_seen", success_seen, "M3-INT-003 必须触发 release-manager-agent 成功分支。")
            passed &= assert_true(assertions, "release_manager_reject_seen", reject_seen, "M3-INT-003 必须触发 release-manager-agent 拒绝分支。")
    else:
        # 未定义 case 进入此分支即视为策略漏洞。
        passed = False
        notes.append("unknown case branch")

    return {
        "status": "pass" if passed else "fail",
        "assertions": assertions,
        "notes": notes,
        "upstream_refs": upstream_refs,
    }


def build_markdown_summary(summary: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Session4 TC Online Summary")
    lines.append("")
    lines.append(f"- ts: {summary.get('ts', '')}")
    lines.append(f"- suite: {summary.get('suite', '')}")
    lines.append(f"- status: {summary.get('status', '')}")
    lines.append(f"- total: {summary.get('total', 0)}")
    lines.append(f"- passed: {summary.get('passed', 0)}")
    lines.append(f"- failed: {summary.get('failed', 0)}")
    lines.append(f"- debug_rounds: {summary.get('debug_rounds', 0)}")
    lines.append("")
    lines.append("## Case Results")
    for case in summary.get("cases", []):
        if not isinstance(case, dict):
            continue
        lines.append(f"- {case.get('id', '')}: {case.get('status', '')} ({case.get('category', '')})")
        detail = case.get("details")
        if isinstance(detail, str) and detail:
            lines.append(f"  - details: {detail}")
        evidence_ref = case.get("evidence_index_ref", "")
        if isinstance(evidence_ref, str) and evidence_ref:
            lines.append(f"  - evidence: {evidence_ref}")
    lines.append("")
    readiness = summary.get("session6_readiness", {})
    if isinstance(readiness, dict) and readiness:
        lines.append("## Session6 Readiness")
        lines.append(f"- ready: {readiness.get('ready', False)}")
        lines.append(f"- decision: {readiness.get('decision', '')}")
        for risk in readiness.get("risks", []) if isinstance(readiness.get("risks"), list) else []:
            lines.append(f"- risk: {risk}")
        lines.append("")
    lines.append("## Conclusion")
    lines.append(summary.get("natural_language_conclusion", ""))
    lines.append("")
    return "\n".join(lines)


def select_upstreams(selected_case_ids: Iterable[str]) -> Set[str]:
    upstreams: Set[str] = set()
    for case_id in selected_case_ids:
        case_def = CASE_BY_ID[case_id]
        if case_def.upstream in {"m3-runtime", "m1-runtime", "session5-runtime"}:
            upstreams.add(case_def.upstream)
    return upstreams


def main() -> int:
    args = parse_args()
    root = repo_root()

    if args.list_cases:
        payload = {
            "cases": [
                {
                    "id": item.case_id,
                    "suite": item.suite,
                    "category": item.category,
                    "status": item.status,
                    "session": item.session,
                    "description": item.description,
                }
                for item in CASES
            ]
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    selection = materialize_selection(args)
    selected_case_ids: List[str] = selection["selected_case_ids"]
    selection_errors: List[str] = selection["errors"]
    suite_inputs: List[str] = selection["suite_inputs"]
    default_mode: bool = selection["default_mode"]

    evidence_root = (root / args.evidence_root).resolve()
    evidence_root.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(evidence_root / "cases", ignore_errors=True)
    (evidence_root / "cases").mkdir(parents=True, exist_ok=True)
    (evidence_root / "upstream" / "m3-runtime").mkdir(parents=True, exist_ok=True)
    (evidence_root / "upstream" / "m1-runtime").mkdir(parents=True, exist_ok=True)
    (evidence_root / "upstream" / "session5-runtime").mkdir(parents=True, exist_ok=True)

    selected_suite_label = "session4-foundation-default" if default_mode else ",".join(suite_inputs) if suite_inputs else "custom-case-selection"

    cases_result: List[Dict[str, Any]] = []
    global_errors: List[str] = []
    reserved_selected: List[str] = []

    if not selected_case_ids:
        global_errors.append("empty_selection:no_case_selected")

    if selection_errors:
        global_errors.extend(selection_errors)

    for case_id in selected_case_ids:
        if CASE_BY_ID[case_id].status == "reserved":
            reserved_selected.append(case_id)
    if reserved_selected:
        global_errors.append(
            "reserved_case_selected:"
            + ",".join(reserved_selected)
            + " (当前会话不可执行)"
        )

    upstream_results: Dict[str, Dict[str, Any]] = {}
    if not global_errors:
        for upstream in sorted(select_upstreams(selected_case_ids)):
            if upstream == "m1-runtime":
                upstream_results[upstream] = run_upstream_m1(root, evidence_root)
            elif upstream == "m3-runtime":
                upstream_results[upstream] = run_upstream_m3(root, evidence_root)
            elif upstream == "session5-runtime":
                upstream_results[upstream] = run_upstream_session5(root)

    for case_id in selected_case_ids:
        case_def = CASE_BY_ID[case_id]
        case_dir = evidence_root / "cases" / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        if case_def.status == "reserved":
            case_payload = {
                "id": case_id,
                "suite": case_def.suite,
                "category": case_def.category,
                "status": "fail",
                "details": "reserved case is not executable in current session",
                "natural_language_conclusion": "该用例属于预留项，当前会话强制执行触发 Fail-Closed。",
                "generated_at": now_iso(),
            }
            case_path = case_dir / "case_result.json"
            dump_json(case_path, case_payload)
            cases_result.append(
                {
                    "id": case_id,
                    "suite": case_def.suite,
                    "category": case_def.category,
                    "status": "fail",
                    "details": case_payload["details"],
                    "evidence_index_ref": to_rel(case_path, root),
                }
            )
            continue

        eval_result = evaluate_case(case_def, upstream_results)
        case_payload = {
            "id": case_id,
            "suite": case_def.suite,
            "category": case_def.category,
            "status": eval_result["status"],
            "description": case_def.description,
            "assertions": eval_result["assertions"],
            "upstream_refs": eval_result["upstream_refs"],
            "notes": eval_result["notes"],
            "generated_at": now_iso(),
        }
        case_path = case_dir / "case_result.json"
        dump_json(case_path, case_payload)
        cases_result.append(
            {
                "id": case_id,
                "suite": case_def.suite,
                "category": case_def.category,
                "status": eval_result["status"],
                "details": "assertions_ok" if eval_result["status"] == "pass" else "assertions_failed",
                "evidence_index_ref": to_rel(case_path, root),
            }
        )

    coverage_required = default_mode or ("all" in suite_inputs)
    covered_categories = {item["category"] for item in cases_result if item["status"] == "pass" and str(item["id"]).startswith("M3-S4-")}
    missing_coverage = [cat for cat in SESSION4_COVERAGE_CLASSES if cat not in covered_categories] if coverage_required else []
    if missing_coverage:
        global_errors.append("missing_session4_coverage:" + ",".join(missing_coverage))

    total = len(cases_result)
    passed = sum(1 for item in cases_result if item["status"] == "pass")
    failed = total - passed
    status = "pass" if (failed == 0 and not global_errors) else "fail"

    session5_upstream = upstream_results.get("session5-runtime", {})
    session5_payload = session5_upstream.get("report_payload", {}) if isinstance(session5_upstream, dict) else {}
    selected_sessions = {CASE_BY_ID[item].session for item in selected_case_ids}
    session5_mode = "session5" in selected_sessions and selected_sessions.issubset({"session5"})

    if session5_mode:
        if status == "pass":
            natural_language_conclusion = "Session5 内部主线 E2E 已通过：主链路、Fail-Closed 后返工、release-manager-agent 双分支均满足。"
        else:
            natural_language_conclusion = "Session5 内部主线 E2E 未通过：仍存在失败用例或闭环证据缺口。"
    else:
        if status == "pass":
            natural_language_conclusion = "Session4 基座已通过：主链路、异常链路、Fail-Closed、回退/返工四类判定均可复用，具备进入 Session5 内部主线 E2E 的准入条件。"
        else:
            natural_language_conclusion = "Session4 基座未通过：存在失败用例或覆盖/策略缺口，暂不具备 Session5 内部主线 E2E 准入条件。"

    summary = {
        "ts": now_iso(),
        "suite": selected_suite_label,
        "status": status,
        "total": total,
        "passed": passed,
        "failed": failed,
        "cases": cases_result,
        "evidence_root": to_rel(evidence_root, root),
        "natural_language_conclusion": natural_language_conclusion,
        "selected_case_ids": selected_case_ids,
        "reserved_case_ids": reserved_selected,
        "errors": global_errors,
        "missing_coverage": missing_coverage,
        "upstream": {
            key: {
                "status": value.get("status"),
                "return_code": value.get("return_code"),
                "report_ref": value.get("report_ref"),
                "command_trace": value.get("command_trace"),
            }
            for key, value in upstream_results.items()
        },
        "debug_rounds": int(session5_payload.get("debug_rounds") or 0),
        "rework_actions": session5_payload.get("rework_actions", []) if isinstance(session5_payload.get("rework_actions"), list) else [],
        "liveness_probes": session5_payload.get("liveness_probes", []) if isinstance(session5_payload.get("liveness_probes"), list) else [],
        "gate_chain_refs": session5_payload.get("gate_chain_refs", []) if isinstance(session5_payload.get("gate_chain_refs"), list) else [],
        "session6_readiness": session5_payload.get("session6_readiness", {}) if isinstance(session5_payload.get("session6_readiness"), dict) else {},
    }

    report_path = evidence_root / args.report
    summary_md_path = evidence_root / DEFAULT_MARKDOWN_NAME
    dump_json(report_path, summary)
    write_text(summary_md_path, build_markdown_summary(summary))

    print(json.dumps(summary, ensure_ascii=False))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
