#!/usr/bin/env python3
"""Run Session3 skill contract validation for impact-analyzer and release-manager."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
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


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run M3 runtime skill contract validation")
    parser.add_argument(
        "--evidence-root",
        default="docs/design/modules/evidence/self-development/runtime-validation-round-session3",
        help="Repo-relative evidence root",
    )
    parser.add_argument(
        "--report",
        default="skill_contract_validation_report.json",
        help="Report filename under evidence root",
    )
    return parser.parse_args()


def check_impact_output(payload: Dict[str, Any]) -> bool:
    required = ["impact_report_ref", "risk_level", "rollback_requirements", "gating_recommendation"]
    for key in required:
        if key not in payload:
            return False
    if str(payload.get("risk_level") or "") not in {"low", "medium", "high", "critical"}:
        return False
    if str(payload.get("gating_recommendation") or "") not in {"allow", "hold", "reject"}:
        return False
    return True


def check_release_output(payload: Dict[str, Any]) -> bool:
    required = ["release_package_ref", "changelog_ref", "release_decision", "rollback_bundle_ref"]
    for key in required:
        if key not in payload:
            return False
    if str(payload.get("release_decision") or "") not in {"approved", "rejected", "blocked"}:
        return False
    return True


def main() -> int:
    args = parse_args()
    root = repo_root()

    evidence_root = (root / args.evidence_root).resolve()
    if evidence_root.exists():
        shutil.rmtree(evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=True)

    cases: List[Dict[str, Any]] = []

    # Shared fixtures
    common_dir = evidence_root / "fixtures"
    common_dir.mkdir(parents=True, exist_ok=True)

    proposal_path = common_dir / "change_proposal.json"
    scope_ok_path = common_dir / "affected_scope_ok.json"
    risk_ok_path = common_dir / "risk_constraints_ok.json"
    risk_conflict_path = common_dir / "risk_constraints_conflict.json"

    dump_json(proposal_path, {"change_id": "chg-m3-s3-001", "summary": "Session3 runtime asset rollout"})
    dump_json(scope_ok_path, {"affected_assets": ["skills/system/impact-analyzer", "skills/system/release-manager"]})
    dump_json(risk_ok_path, {"risk_level": "medium", "rollback_requirements": ["保留回滚补丁", "提供回滚验证记录"]})
    dump_json(risk_conflict_path, {"has_conflict": True, "note": "conflict without adjudication"})

    # TC-IMPACT-HP
    case_dir = evidence_root / "TC-IMPACT-HP"
    case_dir.mkdir(parents=True, exist_ok=True)
    impact_input = case_dir / "input.json"
    impact_output = case_dir / "output.json"
    dump_json(
        impact_input,
        {
            "change_proposal_ref": to_rel(proposal_path, root),
            "affected_scope_ref": to_rel(scope_ok_path, root),
            "risk_constraints_ref": to_rel(risk_ok_path, root),
        },
    )
    proc = run_cmd(
        [
            "python3",
            "skills/system/impact-analyzer/scripts/impact_analyzer_runner.py",
            "--input",
            to_rel(impact_input, root),
            "--output",
            to_rel(impact_output, root),
        ],
        root,
    )
    impact_payload = load_json(impact_output)
    ok = proc.returncode == 0 and check_impact_output(impact_payload)
    cases.append(
        {
            "id": "TC-IMPACT-HP",
            "status": "pass" if ok else "fail",
            "return_code": proc.returncode,
            "output_ref": to_rel(impact_output, root),
            "stderr_tail": "\n".join(proc.stderr.splitlines()[-10:]),
        }
    )

    # TC-IMPACT-FC
    case_dir = evidence_root / "TC-IMPACT-FC"
    case_dir.mkdir(parents=True, exist_ok=True)
    impact_fc_input = case_dir / "input.json"
    impact_fc_output = case_dir / "output.json"
    dump_json(
        impact_fc_input,
        {
            "change_proposal_ref": to_rel(proposal_path, root),
            "affected_scope_ref": "docs/design/modules/evidence/self-development/does-not-exist.json",
            "risk_constraints_ref": to_rel(risk_conflict_path, root),
        },
    )
    proc = run_cmd(
        [
            "python3",
            "skills/system/impact-analyzer/scripts/impact_analyzer_runner.py",
            "--input",
            to_rel(impact_fc_input, root),
            "--output",
            to_rel(impact_fc_output, root),
        ],
        root,
    )
    impact_fc_payload = load_json(impact_fc_output)
    ok = (
        proc.returncode == 2
        and check_impact_output(impact_fc_payload)
        and str(impact_fc_payload.get("gating_recommendation") or "") in {"hold", "reject"}
    )
    cases.append(
        {
            "id": "TC-IMPACT-FC",
            "status": "pass" if ok else "fail",
            "return_code": proc.returncode,
            "output_ref": to_rel(impact_fc_output, root),
            "stderr_tail": "\n".join(proc.stderr.splitlines()[-10:]),
        }
    )

    # Release fixtures
    rollback_ok = common_dir / "rollback_bundle.json"
    gate_pass = common_dir / "final_gate_verdict_pass.json"
    lifecycle_ok = common_dir / "lifecycle_transition.json"
    sync_pass = common_dir / "registry_sync_pass.json"
    sync_fail = common_dir / "registry_sync_fail.json"

    dump_json(rollback_ok, {"bundle_id": "rb-001", "steps": ["restore previous release", "verify health"]})
    dump_json(gate_pass, {"gate_decision": "pass"})
    dump_json(lifecycle_ok, {"transition_status": "succeeded", "to_status": "review"})
    dump_json(sync_pass, {"sync_decision": "pass", "registry_verify_report_ref": "shared/registry/skill_registry.json"})
    dump_json(sync_fail, {"sync_decision": "fail", "registry_verify_report_ref": "shared/registry/skill_registry.json"})

    # TC-RELEASE-HP
    case_dir = evidence_root / "TC-RELEASE-HP"
    case_dir.mkdir(parents=True, exist_ok=True)
    release_input = case_dir / "input.json"
    release_output = case_dir / "output.json"
    release_candidate = case_dir / "candidate_artifacts.json"
    dump_json(
        release_candidate,
        {
            "artifacts": ["dist/release-v1.tar.gz", "docs/changelog.md"],
            "rollback_bundle_ref": to_rel(rollback_ok, root),
        },
    )
    dump_json(
        release_input,
        {
            "candidate_artifacts_ref": to_rel(release_candidate, root),
            "final_gate_verdict_ref": to_rel(gate_pass, root),
            "lifecycle_transition_ref": to_rel(lifecycle_ok, root),
            "registry_sync_ref": to_rel(sync_pass, root),
        },
    )
    proc = run_cmd(
        [
            "python3",
            "skills/system/release-manager/scripts/release_manager_runner.py",
            "--input",
            to_rel(release_input, root),
            "--output",
            to_rel(release_output, root),
        ],
        root,
    )
    release_payload = load_json(release_output)
    ok = proc.returncode == 0 and check_release_output(release_payload) and release_payload.get("release_decision") == "approved"
    cases.append(
        {
            "id": "TC-RELEASE-HP",
            "status": "pass" if ok else "fail",
            "return_code": proc.returncode,
            "output_ref": to_rel(release_output, root),
            "stderr_tail": "\n".join(proc.stderr.splitlines()[-10:]),
        }
    )

    # TC-RELEASE-FC-REG
    case_dir = evidence_root / "TC-RELEASE-FC-REG"
    case_dir.mkdir(parents=True, exist_ok=True)
    reg_input = case_dir / "input.json"
    reg_output = case_dir / "output.json"
    dump_json(
        reg_input,
        {
            "candidate_artifacts_ref": to_rel(release_candidate, root),
            "final_gate_verdict_ref": to_rel(gate_pass, root),
            "lifecycle_transition_ref": to_rel(lifecycle_ok, root),
            "registry_sync_ref": to_rel(sync_fail, root),
        },
    )
    proc = run_cmd(
        [
            "python3",
            "skills/system/release-manager/scripts/release_manager_runner.py",
            "--input",
            to_rel(reg_input, root),
            "--output",
            to_rel(reg_output, root),
        ],
        root,
    )
    reg_payload = load_json(reg_output)
    ok = proc.returncode == 2 and check_release_output(reg_payload) and reg_payload.get("release_decision") == "blocked"
    cases.append(
        {
            "id": "TC-RELEASE-FC-REG",
            "status": "pass" if ok else "fail",
            "return_code": proc.returncode,
            "output_ref": to_rel(reg_output, root),
            "stderr_tail": "\n".join(proc.stderr.splitlines()[-10:]),
        }
    )

    # TC-RELEASE-FC-RB
    case_dir = evidence_root / "TC-RELEASE-FC-RB"
    case_dir.mkdir(parents=True, exist_ok=True)
    rb_input = case_dir / "input.json"
    rb_output = case_dir / "output.json"
    rb_candidate = case_dir / "candidate_artifacts.json"
    dump_json(
        rb_candidate,
        {
            "artifacts": ["dist/release-v2.tar.gz"],
            "rollback_bundle_ref": "docs/design/modules/evidence/self-development/missing-rollback.json",
        },
    )
    dump_json(
        rb_input,
        {
            "candidate_artifacts_ref": to_rel(rb_candidate, root),
            "final_gate_verdict_ref": to_rel(gate_pass, root),
            "lifecycle_transition_ref": to_rel(lifecycle_ok, root),
            "registry_sync_ref": to_rel(sync_pass, root),
        },
    )
    proc = run_cmd(
        [
            "python3",
            "skills/system/release-manager/scripts/release_manager_runner.py",
            "--input",
            to_rel(rb_input, root),
            "--output",
            to_rel(rb_output, root),
        ],
        root,
    )
    rb_payload = load_json(rb_output)
    ok = proc.returncode == 2 and check_release_output(rb_payload) and rb_payload.get("release_decision") == "rejected"
    cases.append(
        {
            "id": "TC-RELEASE-FC-RB",
            "status": "pass" if ok else "fail",
            "return_code": proc.returncode,
            "output_ref": to_rel(rb_output, root),
            "stderr_tail": "\n".join(proc.stderr.splitlines()[-10:]),
        }
    )

    passed = sum(1 for case in cases if case["status"] == "pass")
    failed = len(cases) - passed

    report = {
        "ts": now_iso(),
        "suite": "m3-runtime-skill-contract-validation",
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "cases": cases,
    }

    report_path = evidence_root / args.report
    dump_json(report_path, report)
    print(json.dumps({"report_ref": to_rel(report_path, root), "passed": passed, "failed": failed}, ensure_ascii=False))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
