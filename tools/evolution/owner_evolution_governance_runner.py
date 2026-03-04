#!/usr/bin/env python3
"""Owner 治理提案事件适配器（Phase 1 过渡实现）。

说明：
1. 该适配器只负责把 owner 治理结论产出为标准领域事件 `m5.proposal.*`。
2. 产出遵循 evolution-hook-event-protocol 与 schema 基础字段要求。
3. 这是 Phase 1 过渡实现，流程资产仍以设计文档为准，不改变 registry 生命周期状态。
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class OwnerEvolutionGovernanceError(RuntimeError):
    """Fail-closed runtime error."""


ALLOWED_DECISIONS = {"accepted", "rejected"}


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
        raise OwnerEvolutionGovernanceError("not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def resolve_path(root: Path, raw: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate
    return (root / raw).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise OwnerEvolutionGovernanceError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise OwnerEvolutionGovernanceError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise OwnerEvolutionGovernanceError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit owner-evolution-governance domain event")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--evidence-dir",
        default="",
        help="Evidence directory path (repo-relative). Default runtime_data/execution/evidence/m5-self-evolution/owner-governance/<run_id>",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Optional run id for evidence directory naming",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    request = load_json(resolve_path(root, args.input))
    output_path = resolve_path(root, args.output)

    run_id = args.run_id.strip() or datetime.now(timezone.utc).strftime("owner-governance-%Y%m%dT%H%M%SZ")
    evidence_dir = resolve_path(
        root,
        args.evidence_dir.strip() or f"runtime_data/execution/evidence/m5-self-evolution/owner-governance/{run_id}",
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    decision = str(request.get("proposal_decision") or "").strip().lower()
    if decision not in ALLOWED_DECISIONS:
        raise OwnerEvolutionGovernanceError("proposal_decision_invalid")

    event_name = "m5.proposal.accepted" if decision == "accepted" else "m5.proposal.rejected"
    severity = "info" if decision == "accepted" else "warning"
    timestamp = now_iso()
    bucket = timestamp[:16].replace("-", "").replace(":", "").replace("T", "T")

    owner_agent_id = str(request.get("owner_agent_id") or "owner").strip()
    if not owner_agent_id:
        raise OwnerEvolutionGovernanceError("owner_agent_id_missing")
    asset_ref = str(request.get("asset_ref") or "process:owner-evolution-governance").strip()
    if not asset_ref:
        raise OwnerEvolutionGovernanceError("asset_ref_missing")

    evidence_ref_raw = str(request.get("evidence_ref") or "").strip()
    if evidence_ref_raw:
        evidence_abs = resolve_path(root, evidence_ref_raw)
        if not evidence_abs.exists():
            raise OwnerEvolutionGovernanceError("evidence_ref_unreachable")
    else:
        evidence_abs = evidence_dir / "owner_governance_evidence.json"
        dump_json(
            evidence_abs,
            {
                "timestamp": timestamp,
                "run_id": run_id,
                "proposal_decision": decision,
                "owner_agent_id": owner_agent_id,
                "asset_ref": asset_ref,
            },
        )

    event_id = f"{event_name.replace('.', '-')}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-owner-evolution-governance"
    event_payload = {
        "contract_version": "0.1.0",
        "event_id": event_id,
        "event_name": event_name,
        "event_time": timestamp,
        "module": "m5",
        "trigger_source": "domain-hook",
        "severity": severity,
        "asset_ref": asset_ref,
        "evidence_ref": to_rel(evidence_abs, root),
        "owner_agent_id": owner_agent_id,
        "dedupe_key": f"{event_name}|{asset_ref}|{bucket}",
        "window_bucket": bucket,
        "trace": {
            "process_id": "owner-evolution-governance",
            "adapter": "tools/evolution/owner_evolution_governance_runner.py",
            "proposal_decision": decision,
        },
    }

    event_path = root / "runtime_data/evolution/events" / f"{event_id}.json"
    dump_json(event_path, event_payload)

    result = {
        "status": "ok",
        "run_id": run_id,
        "proposal_decision": decision,
        "domain_event_ref": to_rel(event_path, root),
        "event_name": event_name,
        "evidence_ref": to_rel(evidence_abs, root),
    }
    dump_json(output_path, result)
    print(to_rel(output_path, root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
