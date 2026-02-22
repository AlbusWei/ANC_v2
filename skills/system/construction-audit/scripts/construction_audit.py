#!/usr/bin/env python3
"""Run M6 construction linkage audit and emit structured report."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set


ROUND_ID_RE = re.compile(r"^R-\d{8}-M6-[a-z0-9-]+-\d{2}$")
REPO_REL_RE = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$)).+")
REQUIRED_LINKAGE = {"design", "inventory", "registry", "construction_plane"}


class AuditError(RuntimeError):
    """Fail-closed audit error."""


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
        raise AuditError("Not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AuditError(f"input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AuditError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise AuditError("input payload must be object")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def dump_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def ensure_repo_rel_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or re.match(REPO_REL_RE, value) is None:
        raise AuditError(f"{field} must be repo-relative path without '..': {value!r}")
    return value


def parse_linkage_targets(value: Any) -> Set[str]:
    if isinstance(value, list):
        out: Set[str] = set()
        for item in value:
            if isinstance(item, str) and item.strip():
                out.add(item.strip())
        return out
    if isinstance(value, dict):
        out = set()
        for key, flag in value.items():
            if flag:
                out.add(str(key))
        return out
    return set()


def validate_input(payload: Dict[str, Any], root: Path) -> None:
    required = ["round_id", "scope_baseline_ref", "linkage_targets", "changed_assets", "openspec_ref"]
    for key in required:
        if key not in payload:
            raise AuditError(f"missing required field: {key}")

    round_id = payload["round_id"]
    if not isinstance(round_id, str) or ROUND_ID_RE.match(round_id) is None:
        raise AuditError(f"round_id invalid: {round_id!r}")

    scope_ref = ensure_repo_rel_path(payload["scope_baseline_ref"], "scope_baseline_ref")
    if not (root / scope_ref).exists():
        raise AuditError(f"scope_baseline_ref not reachable: {scope_ref}")

    changed_assets = payload["changed_assets"]
    if not isinstance(changed_assets, list) or not changed_assets:
        raise AuditError("changed_assets must be a non-empty list")

    for idx, path in enumerate(changed_assets):
        ensure_repo_rel_path(path, f"changed_assets[{idx}]")

    openspec_ref = payload["openspec_ref"]
    if not isinstance(openspec_ref, str) or not openspec_ref.strip():
        raise AuditError("openspec_ref must be non-empty string")


def run_audit(payload: Dict[str, Any], root: Path, report_rel: str) -> Dict[str, Any]:
    validate_input(payload, root)

    linkage = parse_linkage_targets(payload["linkage_targets"])
    missing_items: List[str] = []
    blocking_risks: List[str] = []
    recommended_actions: List[str] = []

    missing_scopes = sorted(REQUIRED_LINKAGE - linkage)
    if missing_scopes:
        missing_items.append("linkage_targets missing scopes: " + ", ".join(missing_scopes))
        blocking_risks.append("incomplete linkage scope")
        recommended_actions.append("add missing linkage_targets scopes before proceeding")

    for rel in payload["changed_assets"]:
        if not (root / rel).exists():
            missing_items.append(f"changed asset unreachable: {rel}")
            blocking_risks.append("changed_assets contains unreachable path")
            recommended_actions.append("synchronize changed_assets with actual repo files")

    scope_text = (root / payload["scope_baseline_ref"]).read_text(encoding="utf-8")
    conflict_marked = "semantic_conflict: true" in scope_text or bool(payload.get("semantic_conflict"))
    if conflict_marked and not payload.get("decision_snapshot_ref"):
        blocking_risks.append("openspec semantic conflict unresolved without decision snapshot")
        recommended_actions.append("attach architect decision_snapshot_ref before close")

    if not missing_items and not blocking_risks:
        recommended_actions.append("proceed to AP-034 linked artifacts update")

    decision = "pass" if not blocking_risks else "fail"
    reason = "linkage audit passed" if decision == "pass" else "linkage audit blocked"

    report_lines = [
        "# M6 Construction Linkage Audit Report",
        "",
        f"- timestamp: {now_iso()}",
        f"- round_id: {payload['round_id']}",
        f"- openspec_ref: {payload['openspec_ref']}",
        f"- decision: {decision}",
        f"- reason: {reason}",
        "",
        "## Missing Items",
    ]
    if missing_items:
        for item in missing_items:
            report_lines.append(f"- {item}")
    else:
        report_lines.append("- (none)")

    report_lines.extend(["", "## Blocking Risks"])
    if blocking_risks:
        for item in blocking_risks:
            report_lines.append(f"- {item}")
    else:
        report_lines.append("- (none)")

    report_lines.extend(["", "## Recommended Actions"])
    for item in recommended_actions:
        report_lines.append(f"- {item}")

    dump_text(root / report_rel, "\n".join(report_lines) + "\n")

    result = {
        "linkage_report_ref": report_rel,
        "missing_items": missing_items,
        "blocking_risks": blocking_risks,
        "recommended_actions": recommended_actions,
        "decision": decision,
        "reason": reason,
    }
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run construction linkage audit")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--report", required=True, help="Repo-relative report path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root()

    in_path = Path(args.input)
    if not in_path.is_absolute():
        in_path = root / in_path
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = root / out_path

    try:
        report_rel = ensure_repo_rel_path(args.report, "report")
        payload = load_json(in_path)
        result = run_audit(payload, root, report_rel)
        dump_json(out_path, result)
        print(out_path.relative_to(root).as_posix())
        if result["decision"] != "pass":
            return 3
        return 0
    except AuditError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
