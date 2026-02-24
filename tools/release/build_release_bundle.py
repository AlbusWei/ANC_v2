#!/usr/bin/env python3
"""Build ANC v2 release bundle with fail-closed isolation gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def run(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=False)


def now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    proc = run(["git", "rev-parse", "--show-toplevel"], Path.cwd())
    if proc.returncode != 0:
        raise RuntimeError("not inside git repository")
    return Path(proc.stdout.strip()).resolve()


def require_ok(proc: subprocess.CompletedProcess[str], step: str) -> str:
    if proc.returncode == 0:
        return proc.stdout
    detail = proc.stdout.strip() or proc.stderr.strip() or "unknown error"
    raise RuntimeError(f"{step} failed: {detail}")


def parse_json_output(text: str) -> Dict[str, Any]:
    raw = text.strip()
    if not raw:
        raise RuntimeError("empty JSON output")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON output: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("JSON output root must be object")
    return payload


def git_head(root: Path) -> str:
    proc = run(["git", "rev-parse", "HEAD"], root)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def git_branch(root: Path) -> str:
    proc = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def ensure_clean_worktree(root: Path) -> None:
    proc = run(["git", "status", "--short"], root)
    if proc.returncode != 0:
        raise RuntimeError(f"git status failed: {proc.stderr.strip()}")
    dirty_lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if dirty_lines:
        sample = "\n".join(dirty_lines[:50])
        raise RuntimeError(
            "worktree not clean; commit or stash changes before packaging. "
            f"sample:\n{sample}"
        )


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ANC v2 release bundle")
    parser.add_argument(
        "--output-dir",
        default="runtime_data/exports/release-bundles",
        help="Bundle output root (default: runtime_data/exports/release-bundles)",
    )
    parser.add_argument(
        "--bundle-prefix",
        default="anc-v2-release",
        help="Bundle filename prefix (default: anc-v2-release)",
    )
    parser.add_argument(
        "--verify-openclaw",
        action="store_true",
        help="Run OpenClaw checks in release isolation gate.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow packaging from dirty worktree (not recommended).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    if not args.allow_dirty:
        ensure_clean_worktree(root)

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (root / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    bundle_id = f"{args.bundle_prefix}-{now_compact()}"
    bundle_dir = output_dir / bundle_id
    if bundle_dir.exists():
        raise RuntimeError(f"bundle dir already exists: {bundle_dir}")
    bundle_dir.mkdir(parents=True, exist_ok=False)

    gate_cmd = ["python3", "tools/release/release_isolation_gate.py"]
    if args.verify_openclaw:
        gate_cmd.append("--verify-openclaw")
    gate_stdout = require_ok(run(gate_cmd, root), "release isolation gate")
    gate_result = parse_json_output(gate_stdout)
    if gate_result.get("passed") is not True:
        raise RuntimeError("release isolation gate returned passed=false")

    whitelist_dir = bundle_dir / "whitelist"
    whitelist_cmd = [
        "python3",
        "tools/release/generate_release_whitelist.py",
        "--strict",
        "--output-dir",
        str(whitelist_dir),
    ]
    whitelist_stdout = require_ok(run(whitelist_cmd, root), "release whitelist generation")
    whitelist_result = parse_json_output(whitelist_stdout)
    if whitelist_result.get("ok") is not True:
        raise RuntimeError("release whitelist returned ok=false")

    whitelist_txt_rel = whitelist_result.get("output_txt")
    if not isinstance(whitelist_txt_rel, str) or not whitelist_txt_rel.strip():
        raise RuntimeError("whitelist output_txt missing")
    whitelist_txt = (root / whitelist_txt_rel).resolve()
    if not whitelist_txt.exists():
        raise RuntimeError(f"whitelist txt missing: {whitelist_txt}")

    archive_name = f"{bundle_id}.tar.gz"
    archive_path = bundle_dir / archive_name

    tar_cmd = [
        "tar",
        "-czf",
        str(archive_path),
        "-T",
        str(whitelist_txt),
    ]
    require_ok(run(tar_cmd, root), "tar archive")

    checksum = sha256sum(archive_path)
    checksum_path = bundle_dir / f"{archive_name}.sha256"
    checksum_path.write_text(f"{checksum}  {archive_name}\n", encoding="utf-8")

    manifest: Dict[str, Any] = {
        "generated_at": now_iso(),
        "bundle_id": bundle_id,
        "repo_root": str(root),
        "git": {
            "head": git_head(root),
            "branch": git_branch(root),
            "allow_dirty": bool(args.allow_dirty),
        },
        "inputs": {
            "gate_cmd": gate_cmd,
            "whitelist_cmd": whitelist_cmd,
        },
        "gate": gate_result,
        "whitelist": whitelist_result,
        "outputs": {
            "bundle_dir": str(bundle_dir),
            "archive": str(archive_path),
            "sha256_file": str(checksum_path),
            "sha256": checksum,
        },
    }

    manifest_path = bundle_dir / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = {
        "ok": True,
        "bundle_id": bundle_id,
        "bundle_dir": str(bundle_dir.relative_to(root)),
        "archive": str(archive_path.relative_to(root)),
        "sha256_file": str(checksum_path.relative_to(root)),
        "manifest": str(manifest_path.relative_to(root)),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc))
        raise SystemExit(1)
