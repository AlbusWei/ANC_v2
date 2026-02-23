#!/usr/bin/env python3
"""Executable runner for sys.arch.impact-analyzer."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


class ImpactAnalyzerError(RuntimeError):
    """Fail-closed runtime error for impact-analyzer."""


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
        raise ImpactAnalyzerError("not inside a git repository")
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
        raise ImpactAnalyzerError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ImpactAnalyzerError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ImpactAnalyzerError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run impact-analyzer skill")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--report", default="", help="Impact report output path")
    parser.add_argument("--reject", default="", help="Fail-closed report output path")
    return parser.parse_args()


def _safe_assets(scope_payload: Dict[str, Any]) -> List[str]:
    assets = scope_payload.get("affected_assets")
    if not isinstance(assets, list):
        return []
    normalized: List[str] = []
    for item in assets:
        text = str(item or "").strip()
        if text:
            normalized.append(text)
    return normalized


def _compute_risk_level(assets: List[str], constraints: Dict[str, Any]) -> str:
    explicit = str(constraints.get("risk_level") or "").strip().lower()
    if explicit in {"low", "medium", "high", "critical"}:
        return explicit

    if len(assets) >= 10:
        return "high"
    if len(assets) >= 3:
        return "medium"
    return "low"


def _gating_by_risk(risk_level: str) -> str:
    if risk_level in {"critical"}:
        return "reject"
    if risk_level in {"high"}:
        return "hold"
    return "allow"


def _build_fail_closed(
    *,
    root: Path,
    output_path: Path,
    fail_report_path: Path,
    risk_level: str,
    gating: str,
    reason_code: str,
    reason_detail: str,
) -> int:
    fail_report = {
        "status": "fail_closed",
        "reason_code": reason_code,
        "reason_detail": reason_detail,
        "risk_level": risk_level,
        "gating_recommendation": gating,
        "rollback_requirements": [],
        "generated_at": now_iso(),
    }
    dump_json(fail_report_path, fail_report)
    output = {
        "impact_report_ref": to_rel(fail_report_path, root),
        "risk_level": risk_level,
        "rollback_requirements": [],
        "gating_recommendation": gating,
    }
    dump_json(output_path, output)
    print(to_rel(output_path, root))
    return 2


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    report_path = (
        resolve_path(root, args.report)
        if args.report.strip()
        else output_path.parent / "impact_report.json"
    )
    reject_path = (
        resolve_path(root, args.reject)
        if args.reject.strip()
        else output_path.parent / "impact_reject_report.json"
    )

    request = load_json(input_path)

    for field in ["change_proposal_ref", "affected_scope_ref", "risk_constraints_ref"]:
        value = request.get(field)
        if not isinstance(value, str) or not value.strip():
            return _build_fail_closed(
                root=root,
                output_path=output_path,
                fail_report_path=reject_path,
                risk_level="critical",
                gating="reject",
                reason_code="input_contract_violation",
                reason_detail=f"missing required field: {field}",
            )

    proposal_ref = str(request["change_proposal_ref"]).strip()
    scope_ref = str(request["affected_scope_ref"]).strip()
    risk_ref = str(request["risk_constraints_ref"]).strip()

    try:
        proposal = load_json(resolve_path(root, proposal_ref))
    except ImpactAnalyzerError:
        return _build_fail_closed(
            root=root,
            output_path=output_path,
            fail_report_path=reject_path,
            risk_level="critical",
            gating="reject",
            reason_code="proposal_unparseable",
            reason_detail=f"proposal is missing or invalid: {proposal_ref}",
        )

    try:
        scope_payload = load_json(resolve_path(root, scope_ref))
    except ImpactAnalyzerError:
        return _build_fail_closed(
            root=root,
            output_path=output_path,
            fail_report_path=reject_path,
            risk_level="high",
            gating="hold",
            reason_code="scope_unreachable",
            reason_detail=f"affected scope evidence unreachable: {scope_ref}",
        )

    affected_assets = _safe_assets(scope_payload)
    if not affected_assets:
        return _build_fail_closed(
            root=root,
            output_path=output_path,
            fail_report_path=reject_path,
            risk_level="high",
            gating="hold",
            reason_code="scope_unreachable",
            reason_detail="affected_assets is empty",
        )

    try:
        constraints = load_json(resolve_path(root, risk_ref))
    except ImpactAnalyzerError:
        return _build_fail_closed(
            root=root,
            output_path=output_path,
            fail_report_path=reject_path,
            risk_level="critical",
            gating="reject",
            reason_code="risk_constraints_unparseable",
            reason_detail=f"risk constraints invalid: {risk_ref}",
        )

    conflict = bool(constraints.get("has_conflict") is True or constraints.get("conflict") is True)
    adjudication_ref = str(constraints.get("adjudication_ref") or "").strip()
    if conflict and not adjudication_ref:
        return _build_fail_closed(
            root=root,
            output_path=output_path,
            fail_report_path=reject_path,
            risk_level="critical",
            gating="reject",
            reason_code="risk_conflict_unresolved",
            reason_detail="risk constraints conflict without adjudication_ref",
        )

    risk_level = _compute_risk_level(affected_assets, constraints)
    gating = _gating_by_risk(risk_level)

    rollback_requirements = constraints.get("rollback_requirements")
    if not isinstance(rollback_requirements, list) or not rollback_requirements:
        rollback_requirements = [
            "必须提供可执行回滚脚本或补丁",
            "必须提供回滚触发条件与验证步骤",
        ]

    impact_report = {
        "status": "completed",
        "change_id": proposal.get("change_id") or proposal.get("id") or "unknown-change",
        "proposal_ref": proposal_ref,
        "affected_scope_ref": scope_ref,
        "risk_constraints_ref": risk_ref,
        "affected_assets": affected_assets,
        "risk_level": risk_level,
        "gating_recommendation": gating,
        "rollback_requirements": rollback_requirements,
        "generated_at": now_iso(),
    }
    dump_json(report_path, impact_report)

    output = {
        "impact_report_ref": to_rel(report_path, root),
        "risk_level": risk_level,
        "rollback_requirements": rollback_requirements,
        "gating_recommendation": gating,
    }
    dump_json(output_path, output)
    print(to_rel(output_path, root))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ImpactAnalyzerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
