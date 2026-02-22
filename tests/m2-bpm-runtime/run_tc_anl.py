#!/usr/bin/env python3
"""Run TC-ANL-001~002 for system-analyst P1 minimal runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


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


def _required_handoff_fields() -> List[str]:
    return [
        "instance_id",
        "parent_instance_id",
        "lineage_ref",
        "stack_depth",
        "phase_id",
        "objective_ref",
        "input_ref",
        "output_ref",
        "output_contract",
        "from_role",
        "to_role",
        "acceptance_criteria",
        "deadline",
        "risk_notes",
        "evidence_ref",
    ]


def _read_evidence_refs(index_path: Path) -> Tuple[List[str], List[str]]:
    if not index_path.exists():
        return [], [index_path.as_posix()]
    payload = load_json(index_path)
    refs_raw = payload.get("refs", [])
    if not isinstance(refs_raw, list):
        return [], [index_path.as_posix()]

    refs: List[str] = []
    for item in refs_raw:
        value = str(item or "").strip()
        if value:
            refs.append(value)

    missing: List[str] = []
    root = repo_root()
    for ref in refs:
        if not (root / ref).exists():
            missing.append(ref)
    return refs, missing


def _objective_ref_is_reachable(root: Path, objective_ref: str) -> bool:
    value = str(objective_ref or "").strip()
    if not value:
        return False
    path_only = value.split("#", 1)[0]
    if not path_only:
        return False
    return (root / path_only).exists()


def _reject_payload(
    *,
    handoff: Dict[str, Any],
    reason_code: str,
    missing_fields: List[str],
    missing_evidence_refs: List[str],
    reject_ref: str,
) -> Dict[str, Any]:
    return {
        "status": "rejected",
        "reason_code": reason_code,
        "instance_id": str(handoff.get("instance_id") or "unknown-instance"),
        "missing_fields": missing_fields,
        "missing_evidence_refs": missing_evidence_refs,
        "required_actions": ["补齐handoff字段", "补齐并校验证据索引"],
        "auditable_ref": reject_ref,
        "generated_at": now_iso(),
    }


def run_system_analyst_p1(
    *,
    root: Path,
    handoff_path: Path,
    output_path: Path,
    case_dir: Path,
) -> Dict[str, Any]:
    handoff = load_json(handoff_path)
    missing_fields = [field for field in _required_handoff_fields() if not str(handoff.get(field, "")).strip()]

    if missing_fields:
        reject_path = case_dir / "reject_output.json"
        reject_payload = _reject_payload(
            handoff=handoff,
            reason_code="handoff_contract_violation",
            missing_fields=missing_fields,
            missing_evidence_refs=[],
            reject_ref=rel(reject_path, root),
        )
        dump_json(reject_path, reject_payload)
        dump_json(output_path, {"status": "rejected", "reject_ref": rel(reject_path, root)})
        return {"status": "rejected", "reject_path": reject_path, "digest_path": None}

    if str(handoff.get("to_role")) != "system-analyst":
        reject_path = case_dir / "reject_output.json"
        reject_payload = _reject_payload(
            handoff=handoff,
            reason_code="handoff_contract_violation",
            missing_fields=["to_role(system-analyst)"],
            missing_evidence_refs=[],
            reject_ref=rel(reject_path, root),
        )
        dump_json(reject_path, reject_payload)
        dump_json(output_path, {"status": "rejected", "reject_ref": rel(reject_path, root)})
        return {"status": "rejected", "reject_path": reject_path, "digest_path": None}

    if not _objective_ref_is_reachable(root, str(handoff.get("objective_ref") or "")):
        reject_path = case_dir / "reject_output.json"
        reject_payload = _reject_payload(
            handoff=handoff,
            reason_code="handoff_contract_violation",
            missing_fields=["objective_ref(reachable-path)"],
            missing_evidence_refs=[],
            reject_ref=rel(reject_path, root),
        )
        dump_json(reject_path, reject_payload)
        dump_json(output_path, {"status": "rejected", "reject_ref": rel(reject_path, root)})
        return {"status": "rejected", "reject_path": reject_path, "digest_path": None}

    evidence_ref = str(handoff.get("evidence_ref") or "").strip()
    evidence_index_path = (root / evidence_ref).resolve() if evidence_ref else root / "__missing__"
    evidence_refs, missing_evidence_refs = _read_evidence_refs(evidence_index_path)

    if (not evidence_refs) or missing_evidence_refs:
        reject_path = case_dir / "reject_output.json"
        reject_payload = _reject_payload(
            handoff=handoff,
            reason_code="evidence_insufficient",
            missing_fields=[],
            missing_evidence_refs=missing_evidence_refs if missing_evidence_refs else [evidence_ref],
            reject_ref=rel(reject_path, root),
        )
        dump_json(reject_path, reject_payload)
        dump_json(output_path, {"status": "rejected", "reject_ref": rel(reject_path, root)})
        return {"status": "rejected", "reject_path": reject_path, "digest_path": None}

    seed = f"{handoff.get('instance_id')}|{now_iso()}"
    short_hash = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8]
    digest_id = f"anl-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{short_hash}"

    digest_path = case_dir / "analysis_digest.json"
    digest_payload = {
        "digest_id": digest_id,
        "instance_id": handoff["instance_id"],
        "objective_ref": handoff["objective_ref"],
        "source_handoff_ref": rel(handoff_path, root),
        "summary": "已完成最小证据归纳，输出供 architect/bpm 消费的系统分析摘要。",
        "findings": [
            {
                "signal": "runtime_stability",
                "impact": "中等风险，需要在下一轮治理中跟踪",
                "confidence": "medium",
                "evidence_refs": evidence_refs[:2],
            }
        ],
        "risk_level": "medium",
        "recommendations": [
            {
                "action": "将高风险信号纳入 runtime-policy-calibration 下一轮审查",
                "target_role": "architect",
                "requires_decision": True,
            },
            {
                "action": "由 bpm 安排后续回归窗口并补齐证据采样",
                "target_role": "bpm",
                "requires_decision": True,
            },
        ],
        "generated_at": now_iso(),
    }
    dump_json(digest_path, digest_payload)

    output_payload = {
        "status": "completed",
        "instance_id": handoff["instance_id"],
        "architecture_feedback_digest_ref": rel(digest_path, root),
        "lineage_ref": handoff["lineage_ref"],
        "stack_depth": handoff["stack_depth"],
        "evidence_ref": handoff["evidence_ref"],
        "generated_at": now_iso(),
    }
    dump_json(output_path, output_payload)
    return {"status": "completed", "reject_path": None, "digest_path": digest_path}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TC-ANL-001~002")
    parser.add_argument(
        "--report",
        default="docs/design/modules/evidence/bpm-runtime/w4_tc_anl_report.json",
        help="Repo-relative report output path",
    )
    parser.add_argument(
        "--evidence-root",
        default="docs/design/modules/evidence/bpm-runtime/w4_system_analyst_cases",
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

    agent_doc = (root / args.agent_doc).resolve()
    if not agent_doc.exists():
        raise RuntimeError(f"agent doc not found: {agent_doc}")
    agent_doc_text = agent_doc.read_text(encoding="utf-8")
    required_markers = ["最小输入契约（handoff_in）", "最小输出契约（digest_out / reject_out）", "最小权限边界"]
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
    dump_json(tc1_signal_1, {"signal": "latency_spike", "severity": "medium", "observed_at": now_iso()})
    dump_json(tc1_signal_2, {"signal": "error_burst", "severity": "medium", "observed_at": now_iso()})

    tc1_evidence_index = tc1_dir / "handoff_evidence_index.json"
    dump_json(
        tc1_evidence_index,
        {
            "refs": [
                rel(tc1_signal_1, root),
                rel(tc1_signal_2, root),
            ]
        },
    )

    tc1_handoff = tc1_dir / "handoff_input.json"
    dump_json(
        tc1_handoff,
        {
            "instance_id": "inst-anl-001",
            "parent_instance_id": None,
            "lineage_ref": "docs/design/modules/evidence/bpm-runtime/w4_system_analyst_cases/TC-ANL-001/lineage.json",
            "stack_depth": 1,
            "phase_id": "p1-system-analysis",
            "objective_ref": "docs/design/modules/M2-bpm-engine.md#system-analyst-runtime-calibration",
            "input_ref": rel(tc1_handoff, root),
            "output_ref": rel(tc1_dir / "process_output.json", root),
            "output_contract": "system-analyst.digest.v1",
            "from_role": "bpm",
            "to_role": "system-analyst",
            "acceptance_criteria": ["产出结构化digest", "证据可追溯"],
            "deadline": "2026-02-23T00:00:00Z",
            "risk_notes": ["需要验证证据覆盖度"],
            "evidence_ref": rel(tc1_evidence_index, root),
        },
    )

    tc1_output = tc1_dir / "process_output.json"
    tc1_runtime = run_system_analyst_p1(
        root=root,
        handoff_path=tc1_handoff,
        output_path=tc1_output,
        case_dir=tc1_dir,
    )
    tc1_payload = load_json(tc1_output) if tc1_output.exists() else {}
    tc1_digest_path = tc1_runtime["digest_path"]
    tc1_digest_payload = load_json(tc1_digest_path) if isinstance(tc1_digest_path, Path) and tc1_digest_path.exists() else {}

    tc1_ok = (
        not missing_markers
        and tc1_runtime["status"] == "completed"
        and tc1_payload.get("status") == "completed"
        and isinstance(tc1_payload.get("architecture_feedback_digest_ref"), str)
        and tc1_digest_payload.get("summary")
        and isinstance(tc1_digest_payload.get("findings"), list)
        and isinstance(tc1_digest_payload.get("recommendations"), list)
    )
    append_case(
        cases,
        "TC-ANL-001",
        tc1_ok,
        {
            "doc_markers_missing": missing_markers,
            "runtime_status": tc1_runtime["status"],
            "output_ref": rel(tc1_output, root),
            "digest_ref": tc1_payload.get("architecture_feedback_digest_ref"),
        },
    )

    # TC-ANL-002
    tc2_dir = evidence_root / "TC-ANL-002"
    tc2_dir.mkdir(parents=True, exist_ok=True)

    tc2_evidence_index = tc2_dir / "handoff_evidence_index.json"
    dump_json(tc2_evidence_index, {"refs": [rel(tc2_dir / "signals/missing_signal.json", root)]})

    tc2_handoff = tc2_dir / "handoff_input.json"
    dump_json(
        tc2_handoff,
        {
            "instance_id": "inst-anl-002",
            "parent_instance_id": None,
            "lineage_ref": "docs/design/modules/evidence/bpm-runtime/w4_system_analyst_cases/TC-ANL-002/lineage.json",
            "stack_depth": 1,
            "phase_id": "p1-system-analysis",
            "objective_ref": "docs/design/modules/M2-bpm-engine.md#system-analyst-runtime-calibration",
            "input_ref": rel(tc2_handoff, root),
            "output_ref": rel(tc2_dir / "process_output.json", root),
            "output_contract": "system-analyst.digest.v1",
            "from_role": "architect",
            "to_role": "system-analyst",
            "acceptance_criteria": ["证据不足时拒绝输出"],
            "deadline": "2026-02-23T00:00:00Z",
            "risk_notes": ["证据索引可能空洞"],
            "evidence_ref": rel(tc2_evidence_index, root),
        },
    )

    tc2_output = tc2_dir / "process_output.json"
    tc2_runtime = run_system_analyst_p1(
        root=root,
        handoff_path=tc2_handoff,
        output_path=tc2_output,
        case_dir=tc2_dir,
    )
    tc2_payload = load_json(tc2_output) if tc2_output.exists() else {}
    tc2_reject_path = tc2_runtime["reject_path"]
    tc2_reject_payload = load_json(tc2_reject_path) if isinstance(tc2_reject_path, Path) and tc2_reject_path.exists() else {}

    tc2_ok = (
        tc2_runtime["status"] == "rejected"
        and tc2_payload.get("status") == "rejected"
        and tc2_reject_payload.get("reason_code") == "evidence_insufficient"
        and isinstance(tc2_reject_payload.get("missing_evidence_refs"), list)
        and not (tc2_dir / "analysis_digest.json").exists()
    )
    append_case(
        cases,
        "TC-ANL-002",
        tc2_ok,
        {
            "runtime_status": tc2_runtime["status"],
            "output_ref": rel(tc2_output, root),
            "reject_ref": rel(tc2_reject_path, root) if isinstance(tc2_reject_path, Path) else None,
            "reason_code": tc2_reject_payload.get("reason_code"),
        },
    )

    passed = sum(1 for case in cases if case["status"] == "pass")
    failed = len(cases) - passed

    report_path = (root / args.report).resolve()
    report = {
        "ts": now_iso(),
        "suite": "TC-ANL-001~002",
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "evidence_root": args.evidence_root,
        "agent_doc": args.agent_doc,
        "cases": cases,
    }
    dump_json(report_path, report)

    print(json.dumps(report, ensure_ascii=False))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
