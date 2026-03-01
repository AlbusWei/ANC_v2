#!/usr/bin/env python3
"""release-manager-agent 最小可执行入口。

执行语义：
1. 严格校验 release_request_in 输入契约。
2. 调用 sys.admin.release-manager 技能 runner。
3. 输出 release_delivery_out 或 release_reject_out。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class ReleaseManagerAgentError(RuntimeError):
    """release-manager-agent 的 Fail-Closed 异常。"""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / ".git").exists():
            return parent
    raise ReleaseManagerAgentError("not inside git repository")


def resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else (root / path).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReleaseManagerAgentError(f"missing_file:{path}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseManagerAgentError(f"invalid_json:{path}:{exc}") from exc
    if not isinstance(payload, dict):
        raise ReleaseManagerAgentError("json_root_must_be_object")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run release-manager-agent")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--evidence-dir", default="", help="Evidence dir path")
    parser.add_argument(
        "--release-manager-runner",
        default="skills/system/release-manager/scripts/release_manager_runner.py",
        help="Repo-relative release-manager runner path",
    )
    return parser.parse_args()


def ensure_required_input(payload: Dict[str, Any]) -> Dict[str, str]:
    required = [
        "request_id",
        "objective_ref",
        "candidate_artifacts_ref",
        "final_gate_verdict_ref",
        "lifecycle_transition_ref",
        "registry_sync_ref",
        "release_window",
        "rollback_bundle_ref",
        "requested_by",
        "evidence_ref",
    ]
    parsed: Dict[str, str] = {}
    for field in required:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ReleaseManagerAgentError(f"missing_required_field:{field}")
        parsed[field] = value.strip()
    return parsed


def map_reason_code(raw: str) -> str:
    reason = raw.strip().lower()
    mapping = {
        "gate_not_passed": "gate_failed",
        "registry_sync_failed": "registry_invalid",
        "rollback_unavailable": "rollback_unavailable",
        "missing_prerequisite_evidence": "policy_conflict",
        "candidate_artifacts_empty": "policy_conflict",
    }
    return mapping.get(reason, "policy_conflict")


def build_required_actions(reason_code: str) -> List[str]:
    if reason_code == "gate_failed":
        return ["修复门禁失败项并重新执行质量评测", "补齐 final_gate_verdict 证据后重试发布"]
    if reason_code == "registry_invalid":
        return ["修复 registry 同步失败原因", "重新执行 registry_contract_tool verify 并回填证据"]
    if reason_code == "rollback_unavailable":
        return ["补齐 rollback_bundle_ref 并验证可用性", "重新触发发布打包流程"]
    return ["排查策略冲突并补齐前置证据", "经 owner/bpm 复核后重试"]


def validate_delivery_artifacts(root: Path, release_package_ref: str, changelog_ref: str) -> List[str]:
    issues: List[str] = []
    if not release_package_ref.strip():
        issues.append("release_package_ref_missing")
    if not changelog_ref.strip():
        issues.append("changelog_ref_missing")
    if release_package_ref.strip() and not resolve_path(root, release_package_ref).exists():
        issues.append(f"release_package_ref_unreachable:{release_package_ref}")
    if changelog_ref.strip() and not resolve_path(root, changelog_ref).exists():
        issues.append(f"changelog_ref_unreachable:{changelog_ref}")
    return issues


def write_reject(
    *,
    root: Path,
    output_path: Path,
    request_id: str,
    reason_code: str,
    evidence_ref: str,
    blocking_items: List[str],
) -> int:
    payload = {
        "status": "rejected",
        "release_reject_out": {
            "status": "rejected",
            "request_id": request_id,
            "reason_code": reason_code,
            "blocking_items": blocking_items,
            "required_actions": build_required_actions(reason_code),
            "evidence_ref": evidence_ref,
        },
    }
    dump_json(output_path, payload)
    print(json.dumps({"status": "rejected", "output_ref": to_rel(output_path, root)}, ensure_ascii=False))
    return 2


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    evidence_dir = resolve_path(root, args.evidence_dir) if args.evidence_dir.strip() else (output_path.parent / "release_manager_agent_evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    try:
        request = load_json(input_path)
        parsed = ensure_required_input(request)

        for ref_key in [
            "candidate_artifacts_ref",
            "final_gate_verdict_ref",
            "lifecycle_transition_ref",
            "registry_sync_ref",
            "rollback_bundle_ref",
            "evidence_ref",
        ]:
            path = resolve_path(root, parsed[ref_key])
            if not path.exists():
                return write_reject(
                    root=root,
                    output_path=output_path,
                    request_id=parsed["request_id"],
                    reason_code="policy_conflict",
                    evidence_ref=parsed["evidence_ref"],
                    blocking_items=[f"unreachable:{ref_key}:{parsed[ref_key]}"],
                )

        runner_path = resolve_path(root, args.release_manager_runner)
        if not runner_path.exists():
            raise ReleaseManagerAgentError(f"release_manager_runner_not_found:{runner_path}")

        skill_input = evidence_dir / "release_manager_input.json"
        skill_output = evidence_dir / "release_manager_output.json"
        dump_json(
            skill_input,
            {
                "candidate_artifacts_ref": parsed["candidate_artifacts_ref"],
                "final_gate_verdict_ref": parsed["final_gate_verdict_ref"],
                "lifecycle_transition_ref": parsed["lifecycle_transition_ref"],
                "registry_sync_ref": parsed["registry_sync_ref"],
            },
        )

        cmd = [
            sys.executable,
            to_rel(runner_path, root),
            "--input",
            to_rel(skill_input, root),
            "--output",
            to_rel(skill_output, root),
        ]
        proc = run_cmd(cmd, root)
        (evidence_dir / "release_manager.stdout.log").write_text(proc.stdout, encoding="utf-8")
        (evidence_dir / "release_manager.stderr.log").write_text(proc.stderr, encoding="utf-8")

        if not skill_output.exists():
            raise ReleaseManagerAgentError("release_manager_output_missing")

        skill_payload = load_json(skill_output)
        decision = str(skill_payload.get("release_decision") or "").strip().lower()
        runtime_evidence_ref = to_rel(skill_output, root)

        if proc.returncode == 0 and decision == "approved":
            release_package_ref = str(skill_payload.get("release_package_ref") or "")
            changelog_ref = str(skill_payload.get("changelog_ref") or "")
            delivery = {
                "status": "delivered",
                "request_id": parsed["request_id"],
                "release_package_ref": release_package_ref,
                "changelog_ref": changelog_ref,
                "release_decision": "approved",
                "published_at": now_iso(),
                "evidence_ref": runtime_evidence_ref,
            }
            delivery_issues = validate_delivery_artifacts(root, release_package_ref, changelog_ref)
            if delivery_issues:
                return write_reject(
                    root=root,
                    output_path=output_path,
                    request_id=parsed["request_id"],
                    reason_code="policy_conflict",
                    evidence_ref=runtime_evidence_ref,
                    blocking_items=delivery_issues,
                )

            dump_json(
                output_path,
                {
                    "status": "delivered",
                    "release_delivery_out": delivery,
                },
            )
            print(json.dumps({"status": "delivered", "output_ref": to_rel(output_path, root)}, ensure_ascii=False))
            return 0

        reason_code = map_reason_code(str(skill_payload.get("reason_code") or ""))
        return write_reject(
            root=root,
            output_path=output_path,
            request_id=parsed["request_id"],
            reason_code=reason_code,
            evidence_ref=runtime_evidence_ref,
            blocking_items=[f"release_manager_decision={decision or 'unknown'}", f"release_manager_rc={proc.returncode}"],
        )
    except ReleaseManagerAgentError as exc:
        fail_payload = {
            "timestamp": now_iso(),
            "status": "failed",
            "reason": str(exc),
            "fail_closed": True,
        }
        fail_record = evidence_dir / "fail_closed_record.json"
        dump_json(fail_record, fail_payload)
        dump_json(
            output_path,
            {
                "status": "rejected",
                "release_reject_out": {
                    "status": "rejected",
                    "request_id": "",
                    "reason_code": "policy_conflict",
                    "blocking_items": [str(exc)],
                    "required_actions": build_required_actions("policy_conflict"),
                    "evidence_ref": to_rel(fail_record, root),
                },
                "fail_closed_record_ref": to_rel(fail_record, root),
            },
        )
        print(json.dumps({"status": "rejected", "output_ref": to_rel(output_path, root)}, ensure_ascii=False))
        return 2
    except Exception as exc:  # noqa: BLE001
        dump_json(
            output_path,
            {
                "status": "error",
                "reason_code": "unexpected_error",
                "error": str(exc),
            },
        )
        print(json.dumps({"status": "error", "output_ref": to_rel(output_path, root)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
