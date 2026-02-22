#!/usr/bin/env python3
"""Run TC-ANL-001~003 for system-analyst production runtime."""

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
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("not inside git repository")
    return Path(proc.stdout.strip()).resolve()


def run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"json root must be object: {path}")
    return payload


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def append_case(cases: List[Dict[str, Any]], case_id: str, ok: bool, details: Dict[str, Any]) -> None:
    cases.append({"id": case_id, "status": "pass" if ok else "fail", "details": details})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TC-ANL-001~003")
    parser.add_argument(
        "--digest-runner",
        default="skills/system/system-feedback-digest/scripts/system_feedback_digest_runner.py",
        help="Repo-relative digest runner path",
    )
    parser.add_argument(
        "--process-runner",
        default="processes/meta/runtime-policy-calibration/scripts/runtime_policy_calibration_runner.py",
        help="Repo-relative runtime-policy-calibration runner path",
    )
    parser.add_argument(
        "--report",
        default="docs/design/modules/evidence/bpm-runtime/w5_tc_anl_report.json",
        help="Repo-relative report output path",
    )
    parser.add_argument(
        "--evidence-root",
        default="docs/design/modules/evidence/bpm-runtime/w5_system_analyst_prod_cases",
        help="Repo-relative evidence root",
    )
    parser.add_argument(
        "--agent-doc",
        default="docs/design/agents/kernel/system-analyst.md",
        help="Repo-relative system-analyst design doc path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    digest_runner = (root / args.digest_runner).resolve()
    process_runner = (root / args.process_runner).resolve()
    if not digest_runner.exists():
        raise RuntimeError(f"digest runner not found: {digest_runner}")
    if not process_runner.exists():
        raise RuntimeError(f"process runner not found: {process_runner}")

    agent_doc = (root / args.agent_doc).resolve()
    if not agent_doc.exists():
        raise RuntimeError(f"agent doc not found: {agent_doc}")
    agent_doc_text = agent_doc.read_text(encoding="utf-8")
    required_markers = [
        "最小输入契约（handoff_in）",
        "最小输出契约（digest_out / reject_out）",
        "最小权限边界",
        "sys.arch.system-feedback-digest",
    ]
    missing_markers = [marker for marker in required_markers if marker not in agent_doc_text]

    evidence_root = (root / args.evidence_root).resolve()
    if evidence_root.exists():
        shutil.rmtree(evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=True)

    cases: List[Dict[str, Any]] = []

    # TC-ANL-001
    tc1_dir = evidence_root / "TC-ANL-001"
    tc1_dir.mkdir(parents=True, exist_ok=True)

    tc1_signal_1 = tc1_dir / "signals/runtime_signal.json"
    tc1_signal_2 = tc1_dir / "signals/incident_summary.json"
    dump_json(tc1_signal_1, {"signal": "latency_spike", "severity": "high", "impact": "请求响应抖动", "observed_at": now_iso()})
    dump_json(tc1_signal_2, {"signal": "error_burst", "severity": "medium", "impact": "错误率升高", "observed_at": now_iso()})

    tc1_index = tc1_dir / "handoff_evidence_index.json"
    dump_json(tc1_index, {"refs": [rel(tc1_signal_1, root), rel(tc1_signal_2, root)]})

    tc1_handoff = tc1_dir / "handoff_input.json"
    dump_json(
        tc1_handoff,
        {
            "instance_id": "inst-anl-prod-001",
            "parent_instance_id": None,
            "lineage_ref": rel(tc1_dir / "lineage.json", root),
            "stack_depth": 1,
            "phase_id": "p3-posterior-analysis-and-hypothesis",
            "objective_ref": "docs/design/processes/runtime-policy-calibration-process.md#目标",
            "input_ref": rel(tc1_handoff, root),
            "output_ref": rel(tc1_dir / "digest_output.json", root),
            "output_contract": "system-analyst.digest.v1",
            "from_role": "bpm",
            "to_role": "system-analyst",
            "acceptance_criteria": ["产出结构化digest", "建议可治理消费"],
            "deadline": "2026-02-23T12:00:00Z",
            "risk_notes": ["高风险信号需要审批链"],
            "evidence_ref": rel(tc1_index, root),
        },
    )

    tc1_input = tc1_dir / "digest_input.json"
    tc1_output = tc1_dir / "digest_output.json"
    tc1_digest = tc1_dir / "analysis_digest.json"
    tc1_reject = tc1_dir / "reject_output.json"
    dump_json(tc1_input, {"handoff_ref": rel(tc1_handoff, root), "analysis_scope": "runtime-policy-calibration"})

    tc1_cmd = [
        sys.executable,
        str(digest_runner),
        "--input",
        str(tc1_input),
        "--output",
        str(tc1_output),
        "--digest",
        str(tc1_digest),
        "--reject",
        str(tc1_reject),
    ]
    tc1_proc = run_cmd(tc1_cmd, root)
    tc1_payload = load_json(tc1_output) if tc1_output.exists() else {}
    tc1_digest_payload = load_json(tc1_digest) if tc1_digest.exists() else {}

    tc1_ok = (
        not missing_markers
        and tc1_proc.returncode == 0
        and tc1_payload.get("status") == "completed"
        and tc1_digest.exists()
        and isinstance(tc1_digest_payload.get("findings"), list)
        and isinstance(tc1_digest_payload.get("recommendations"), list)
    )
    append_case(
        cases,
        "TC-ANL-001",
        tc1_ok,
        {
            "doc_markers_missing": missing_markers,
            "return_code": tc1_proc.returncode,
            "stdout": tc1_proc.stdout.strip(),
            "stderr": tc1_proc.stderr.strip(),
            "digest_ref": tc1_payload.get("architecture_feedback_digest_ref"),
        },
    )

    # TC-ANL-002
    tc2_dir = evidence_root / "TC-ANL-002"
    tc2_dir.mkdir(parents=True, exist_ok=True)

    tc2_index = tc2_dir / "handoff_evidence_index.json"
    dump_json(tc2_index, {"refs": [rel(tc2_dir / "signals/missing_signal.json", root)]})

    tc2_handoff = tc2_dir / "handoff_input.json"
    dump_json(
        tc2_handoff,
        {
            "instance_id": "inst-anl-prod-002",
            "parent_instance_id": None,
            "lineage_ref": rel(tc2_dir / "lineage.json", root),
            "stack_depth": 1,
            "phase_id": "p3-posterior-analysis-and-hypothesis",
            "objective_ref": "docs/design/processes/runtime-policy-calibration-process.md#目标",
            "input_ref": rel(tc2_handoff, root),
            "output_ref": rel(tc2_dir / "digest_output.json", root),
            "output_contract": "system-analyst.digest.v1",
            "from_role": "architect",
            "to_role": "system-analyst",
            "acceptance_criteria": ["证据不足时拒绝"],
            "deadline": "2026-02-23T12:00:00Z",
            "risk_notes": ["缺证据场景"],
            "evidence_ref": rel(tc2_index, root),
        },
    )

    tc2_input = tc2_dir / "digest_input.json"
    tc2_output = tc2_dir / "digest_output.json"
    tc2_digest = tc2_dir / "analysis_digest.json"
    tc2_reject = tc2_dir / "reject_output.json"
    dump_json(tc2_input, {"handoff_ref": rel(tc2_handoff, root), "analysis_scope": "runtime-policy-calibration"})

    tc2_cmd = [
        sys.executable,
        str(digest_runner),
        "--input",
        str(tc2_input),
        "--output",
        str(tc2_output),
        "--digest",
        str(tc2_digest),
        "--reject",
        str(tc2_reject),
    ]
    tc2_proc = run_cmd(tc2_cmd, root)
    tc2_payload = load_json(tc2_output) if tc2_output.exists() else {}
    tc2_reject_payload = load_json(tc2_reject) if tc2_reject.exists() else {}

    tc2_ok = (
        tc2_proc.returncode == 2
        and tc2_payload.get("status") == "rejected"
        and tc2_reject_payload.get("reason_code") == "evidence_insufficient"
        and not tc2_digest.exists()
    )
    append_case(
        cases,
        "TC-ANL-002",
        tc2_ok,
        {
            "return_code": tc2_proc.returncode,
            "stdout": tc2_proc.stdout.strip(),
            "stderr": tc2_proc.stderr.strip(),
            "reject_ref": tc2_payload.get("reject_ref"),
            "reason_code": tc2_reject_payload.get("reason_code"),
        },
    )

    # TC-ANL-003
    tc3_dir = evidence_root / "TC-ANL-003"
    tc3_dir.mkdir(parents=True, exist_ok=True)

    tc3_issue = tc3_dir / "issue.json"
    tc3_policy = tc3_dir / "current_policy.json"
    tc3_constraints = tc3_dir / "risk_constraints.json"
    tc3_signal_1 = tc3_dir / "signals/runtime_latency.json"
    tc3_signal_2 = tc3_dir / "signals/runtime_error.json"
    tc3_index = tc3_dir / "handoff_evidence_index.json"
    tc3_handoff = tc3_dir / "handoff_input.json"

    dump_json(
        tc3_issue,
        {
            "issue_id": "rpc-issue-001",
            "scope": "m2-catchup-window-calibration",
            "objective_ref": "docs/design/processes/runtime-policy-calibration-process.md#目标",
        },
    )
    dump_json(tc3_policy, {"policy_id": "catchup-policy-v3", "window_minutes": {"high": 5, "medium": 15, "low": 30}})
    dump_json(tc3_constraints, {"high_risk_requires_admin_approval": True, "min_sample_count": 2})
    dump_json(tc3_signal_1, {"signal": "catchup_delay", "severity": "high", "impact": "高风险漏跑窗口超时"})
    dump_json(tc3_signal_2, {"signal": "retry_pressure", "severity": "medium", "impact": "重试负载升高"})
    dump_json(tc3_index, {"refs": [rel(tc3_signal_1, root), rel(tc3_signal_2, root)]})
    dump_json(
        tc3_handoff,
        {
            "instance_id": "inst-anl-prod-003",
            "parent_instance_id": None,
            "lineage_ref": rel(tc3_dir / "lineage.json", root),
            "stack_depth": 2,
            "phase_id": "p3-posterior-analysis-and-hypothesis",
            "objective_ref": "docs/design/processes/runtime-policy-calibration-process.md#目标",
            "input_ref": rel(tc3_handoff, root),
            "output_ref": rel(tc3_dir / "process_output.json", root),
            "output_contract": "system-analyst.digest.v1",
            "from_role": "bpm",
            "to_role": "system-analyst",
            "acceptance_criteria": ["产出策略校准提案"],
            "deadline": "2026-02-23T12:00:00Z",
            "risk_notes": ["高风险变更需admin审批"],
            "evidence_ref": rel(tc3_index, root),
        },
    )

    tc3_input = tc3_dir / "process_input.json"
    tc3_output = tc3_dir / "process_output.json"
    dump_json(
        tc3_input,
        {
            "issue_ref": rel(tc3_issue, root),
            "runtime_evidence_refs": [rel(tc3_signal_1, root), rel(tc3_signal_2, root)],
            "current_policy_ref": rel(tc3_policy, root),
            "risk_constraints_ref": rel(tc3_constraints, root),
            "handoff_ref": rel(tc3_handoff, root),
            "admin_approved": True,
        },
    )

    tc3_cmd = [
        sys.executable,
        str(process_runner),
        "--input",
        str(tc3_input),
        "--output",
        str(tc3_output),
        "--evidence-dir",
        rel(tc3_dir / "runtime_policy_calibration", root),
        "--run-id",
        "TC-ANL-003",
        "--digest-runner",
        str(digest_runner),
    ]
    tc3_proc = run_cmd(tc3_cmd, root)
    tc3_payload = load_json(tc3_output) if tc3_output.exists() else {}

    tc3_required_refs = [
        "calibration_report_ref",
        "policy_change_proposal_ref",
        "governance_sync_minutes_ref",
        "decision_record_ref",
        "rollout_observation_ref",
        "runtime_trace_ref",
    ]
    tc3_refs_reachable = True
    for key in tc3_required_refs:
        ref = tc3_payload.get(key)
        if not isinstance(ref, str) or not (root / ref).exists():
            tc3_refs_reachable = False
            break

    tc3_ok = tc3_proc.returncode == 0 and tc3_payload.get("status") == "ok" and tc3_refs_reachable
    append_case(
        cases,
        "TC-ANL-003",
        tc3_ok,
        {
            "return_code": tc3_proc.returncode,
            "stdout": tc3_proc.stdout.strip(),
            "stderr": tc3_proc.stderr.strip(),
            "runtime_trace_ref": tc3_payload.get("runtime_trace_ref"),
            "decision_record_ref": tc3_payload.get("decision_record_ref"),
        },
    )

    passed = sum(1 for case in cases if case["status"] == "pass")
    failed = len(cases) - passed

    report_path = (root / args.report).resolve()
    report = {
        "ts": now_iso(),
        "suite": "TC-ANL-001~003",
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "evidence_root": args.evidence_root,
        "agent_doc": args.agent_doc,
        "digest_runner": args.digest_runner,
        "process_runner": args.process_runner,
        "cases": cases,
    }
    dump_json(report_path, report)

    print(json.dumps(report, ensure_ascii=False))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
