#!/usr/bin/env python3
"""Executable runner for sys.arch.system-feedback-digest."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


class SystemFeedbackDigestError(RuntimeError):
    """Fail-closed runtime error for system-feedback-digest."""


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
        raise SystemFeedbackDigestError("not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemFeedbackDigestError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemFeedbackDigestError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemFeedbackDigestError(f"json root must be object: {path}")
    return payload


def required_handoff_fields() -> List[str]:
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


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return len(value) == 0
    return False


def objective_ref_reachable(root: Path, objective_ref: str) -> bool:
    value = str(objective_ref or "").strip()
    if not value:
        return False
    path_only = value.split("#", 1)[0]
    if not path_only:
        return False
    return (root / path_only).exists()


def parse_evidence_index(root: Path, evidence_ref: str) -> Tuple[List[str], List[str]]:
    index_path = resolve_path(root, evidence_ref)
    payload = load_json(index_path)
    refs = payload.get("refs")
    if not isinstance(refs, list):
        return [], [evidence_ref]

    evidence_refs: List[str] = []
    missing: List[str] = []
    for item in refs:
        ref = str(item or "").strip()
        if not ref:
            continue
        evidence_refs.append(ref)
        if not resolve_path(root, ref).exists():
            missing.append(ref)
    return evidence_refs, missing


def summarize_evidence(root: Path, refs: List[str], max_findings: int) -> Tuple[List[Dict[str, Any]], str]:
    findings: List[Dict[str, Any]] = []
    severity_level = "low"

    for ref in refs[:max_findings]:
        path = resolve_path(root, ref)
        signal = path.stem
        impact = "观察到运行波动"
        confidence = "medium"
        severity = "medium"

        if path.suffix.lower() == ".json":
            payload = load_json(path)
            signal = str(payload.get("signal") or payload.get("event") or signal)
            severity = str(payload.get("severity") or payload.get("risk") or "medium").lower()
            impact = str(payload.get("impact") or payload.get("note") or impact)
            if severity not in {"low", "medium", "high"}:
                severity = "medium"

        if severity == "high":
            severity_level = "high"
            confidence = "high"
        elif severity == "medium" and severity_level != "high":
            severity_level = "medium"

        findings.append(
            {
                "signal": signal,
                "impact": impact,
                "confidence": confidence,
                "evidence_refs": [ref],
            }
        )

    return findings, severity_level


def build_reject(
    *,
    root: Path,
    output_path: Path,
    reject_path: Path,
    handoff: Dict[str, Any],
    reason_code: str,
    missing_fields: List[str],
    missing_evidence_refs: List[str],
) -> int:
    reject_payload = {
        "status": "rejected",
        "reason_code": reason_code,
        "instance_id": str(handoff.get("instance_id") or "unknown-instance"),
        "missing_fields": missing_fields,
        "missing_evidence_refs": missing_evidence_refs,
        "required_actions": ["补齐handoff字段", "补齐并校验证据索引"],
        "auditable_ref": to_rel(reject_path, root),
        "generated_at": now_iso(),
    }
    dump_json(reject_path, reject_payload)
    dump_json(
        output_path,
        {
            "status": "rejected",
            "instance_id": str(handoff.get("instance_id") or "unknown-instance"),
            "reject_ref": to_rel(reject_path, root),
            "generated_at": now_iso(),
        },
    )
    print(to_rel(output_path, root))
    return 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run system-feedback-digest skill")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--digest", default="", help="Digest output JSON path")
    parser.add_argument("--reject", default="", help="Reject output JSON path")
    parser.add_argument("--max-findings", type=int, default=5, help="Maximum findings in digest")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    request = load_json(input_path)

    handoff_ref = str(request.get("handoff_ref") or "").strip()
    if not handoff_ref:
        raise SystemFeedbackDigestError("missing handoff_ref")
    handoff = load_json(resolve_path(root, handoff_ref))

    digest_path = resolve_path(root, args.digest) if args.digest.strip() else output_path.parent / "analysis_digest.json"
    reject_path = resolve_path(root, args.reject) if args.reject.strip() else output_path.parent / "reject_output.json"

    missing_fields: List[str] = []
    for field in required_handoff_fields():
        if field not in handoff:
            missing_fields.append(field)
            continue
        if field == "parent_instance_id":
            continue
        if is_blank(handoff.get(field)):
            missing_fields.append(field)

    if missing_fields:
        return build_reject(
            root=root,
            output_path=output_path,
            reject_path=reject_path,
            handoff=handoff,
            reason_code="handoff_contract_violation",
            missing_fields=missing_fields,
            missing_evidence_refs=[],
        )

    if str(handoff.get("to_role")) != "system-analyst":
        return build_reject(
            root=root,
            output_path=output_path,
            reject_path=reject_path,
            handoff=handoff,
            reason_code="handoff_contract_violation",
            missing_fields=["to_role(system-analyst)"],
            missing_evidence_refs=[],
        )

    if not objective_ref_reachable(root, str(handoff.get("objective_ref") or "")):
        return build_reject(
            root=root,
            output_path=output_path,
            reject_path=reject_path,
            handoff=handoff,
            reason_code="handoff_contract_violation",
            missing_fields=["objective_ref(reachable-path)"],
            missing_evidence_refs=[],
        )

    evidence_ref = str(handoff.get("evidence_ref") or "").strip()
    try:
        evidence_refs, missing_evidence_refs = parse_evidence_index(root, evidence_ref)
    except SystemFeedbackDigestError:
        evidence_refs, missing_evidence_refs = [], [evidence_ref]

    if (not evidence_refs) or missing_evidence_refs:
        return build_reject(
            root=root,
            output_path=output_path,
            reject_path=reject_path,
            handoff=handoff,
            reason_code="evidence_insufficient",
            missing_fields=[],
            missing_evidence_refs=missing_evidence_refs if missing_evidence_refs else [evidence_ref],
        )

    findings, risk_level = summarize_evidence(root, evidence_refs, max(1, args.max_findings))

    digest_seed = f"{handoff['instance_id']}|{handoff['lineage_ref']}|{now_iso()}"
    digest_id = f"anl-{hashlib.sha256(digest_seed.encode('utf-8')).hexdigest()[:16]}"

    recommendations: List[Dict[str, Any]] = [
        {
            "action": "将高优先级信号同步到 runtime-policy-calibration 决策会",
            "target_role": "architect",
            "requires_decision": True,
        },
        {
            "action": "由 bpm 安排下一轮回归采样并补齐策略观测窗口",
            "target_role": "bpm",
            "requires_decision": True,
        },
    ]
    if risk_level == "high":
        recommendations.append(
            {
                "action": "高风险策略变更需 admin 明确审批后再执行",
                "target_role": "admin",
                "requires_decision": True,
            }
        )

    digest_payload = {
        "digest_id": digest_id,
        "instance_id": handoff["instance_id"],
        "objective_ref": handoff["objective_ref"],
        "source_handoff_ref": handoff_ref,
        "summary": "已完成系统级后验证据归纳，可用于治理决策同步。",
        "findings": findings,
        "risk_level": risk_level,
        "recommendations": recommendations,
        "generated_at": now_iso(),
    }
    dump_json(digest_path, digest_payload)

    output_payload = {
        "status": "completed",
        "instance_id": handoff["instance_id"],
        "lineage_ref": handoff["lineage_ref"],
        "stack_depth": handoff["stack_depth"],
        "architecture_feedback_digest_ref": to_rel(digest_path, root),
        "generated_at": now_iso(),
    }
    dump_json(output_path, output_payload)

    print(to_rel(output_path, root))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemFeedbackDigestError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
