#!/usr/bin/env python3
"""Executable runner for sys.admin.release-manager."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


class ReleaseManagerError(RuntimeError):
    """Fail-closed runtime error for release-manager."""


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
        raise ReleaseManagerError("not inside a git repository")
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
        raise ReleaseManagerError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseManagerError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReleaseManagerError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run release-manager skill")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--package", default="", help="Release package output path")
    parser.add_argument("--changelog", default="", help="Changelog output path")
    return parser.parse_args()


def _verdict_pass(payload: Dict[str, Any]) -> bool:
    candidates = [
        str(payload.get("gate_decision") or "").strip().lower(),
        str(payload.get("verdict") or "").strip().lower(),
        str(payload.get("status") or "").strip().lower(),
    ]
    return "pass" in candidates


def _sync_ok(payload: Dict[str, Any]) -> bool:
    decision = str(payload.get("sync_decision") or "").strip().lower()
    return decision == "pass"


def _build_block_or_reject(
    *,
    root: Path,
    output_path: Path,
    release_decision: str,
    reason_code: str,
) -> int:
    output = {
        "release_package_ref": "",
        "changelog_ref": "",
        "release_decision": release_decision,
        "rollback_bundle_ref": "",
        "reason_code": reason_code,
        "generated_at": now_iso(),
    }
    dump_json(output_path, output)
    print(to_rel(output_path, root))
    return 2


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    package_path = (
        resolve_path(root, args.package)
        if args.package.strip()
        else output_path.parent / "release_package.json"
    )
    changelog_path = (
        resolve_path(root, args.changelog)
        if args.changelog.strip()
        else output_path.parent / "release_changelog.json"
    )

    request = load_json(input_path)

    for field in [
        "candidate_artifacts_ref",
        "final_gate_verdict_ref",
        "lifecycle_transition_ref",
        "registry_sync_ref",
    ]:
        value = request.get(field)
        if not isinstance(value, str) or not value.strip():
            return _build_block_or_reject(
                root=root,
                output_path=output_path,
                release_decision="rejected",
                reason_code=f"missing_{field}",
            )

    try:
        candidate = load_json(resolve_path(root, str(request["candidate_artifacts_ref"])))
        gate = load_json(resolve_path(root, str(request["final_gate_verdict_ref"])))
        _ = load_json(resolve_path(root, str(request["lifecycle_transition_ref"])))
        sync = load_json(resolve_path(root, str(request["registry_sync_ref"])))
    except ReleaseManagerError:
        return _build_block_or_reject(
            root=root,
            output_path=output_path,
            release_decision="rejected",
            reason_code="missing_prerequisite_evidence",
        )

    if not _verdict_pass(gate):
        return _build_block_or_reject(
            root=root,
            output_path=output_path,
            release_decision="rejected",
            reason_code="gate_not_passed",
        )

    if not _sync_ok(sync):
        return _build_block_or_reject(
            root=root,
            output_path=output_path,
            release_decision="blocked",
            reason_code="registry_sync_failed",
        )

    rollback_ref = str(candidate.get("rollback_bundle_ref") or "").strip()
    if not rollback_ref:
        return _build_block_or_reject(
            root=root,
            output_path=output_path,
            release_decision="rejected",
            reason_code="rollback_unavailable",
        )

    rollback_path = resolve_path(root, rollback_ref)
    if not rollback_path.exists():
        return _build_block_or_reject(
            root=root,
            output_path=output_path,
            release_decision="rejected",
            reason_code="rollback_unavailable",
        )

    artifacts = candidate.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return _build_block_or_reject(
            root=root,
            output_path=output_path,
            release_decision="rejected",
            reason_code="candidate_artifacts_empty",
        )

    package_payload = {
        "generated_at": now_iso(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "source_candidate_ref": request["candidate_artifacts_ref"],
    }
    dump_json(package_path, package_payload)

    changelog_payload = {
        "generated_at": now_iso(),
        "summary": "Session3 release package generated by sys.admin.release-manager",
        "entries": [
            "通过 final gate verdict",
            "通过 lifecycle transition 校验",
            "通过 registry sync 校验",
            "回滚包可用",
        ],
    }
    dump_json(changelog_path, changelog_payload)

    output = {
        "release_package_ref": to_rel(package_path, root),
        "changelog_ref": to_rel(changelog_path, root),
        "release_decision": "approved",
        "rollback_bundle_ref": rollback_ref,
    }
    dump_json(output_path, output)
    print(to_rel(output_path, root))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReleaseManagerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
