#!/usr/bin/env python3
"""Release isolation gate for ANC v2.

Fail-Closed checks:
1. Public evidence dir only keeps README.
2. Legacy evidence path references are fully migrated (except explicit policy docs).
3. Registry/config fragments do not reference runtime_data/private-assets.
4. Registry contract verification passes.
5. Optional OpenClaw scope dry-run checks pass.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def run(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=False)


def repo_root() -> Path:
    proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError("not inside git repo")
    return Path(proc.stdout.strip()).resolve()


def check_public_evidence_placeholder(root: Path) -> CheckResult:
    evidence_dir = root / "docs/design/modules/evidence"
    if not evidence_dir.exists():
        return CheckResult("public_evidence_placeholder", False, "missing docs/design/modules/evidence")

    files = [p for p in evidence_dir.rglob("*") if p.is_file()]
    allowed = {evidence_dir / "README.md"}
    extra = [p for p in files if p not in allowed]
    if extra:
        sample = ", ".join(str(p.relative_to(root)) for p in extra[:5])
        return CheckResult(
            "public_evidence_placeholder",
            False,
            f"public evidence dir contains non-whitelist files (sample): {sample}",
        )
    return CheckResult("public_evidence_placeholder", True, "docs/design/modules/evidence only keeps README.md")


def check_legacy_path_refs(root: Path) -> CheckResult:
    cmd = [
        "rg",
        "-n",
        "docs/design/modules/evidence/",
        "--glob",
        "!docs/design/modules/evidence/**",
        "-g",
        "*.py",
        "-g",
        "*.md",
        "-g",
        "*.json",
        "-g",
        "*.sh",
    ]
    proc = run(cmd, root)
    if proc.returncode not in {0, 1}:
        return CheckResult("legacy_path_refs", False, f"rg failed: {proc.stderr.strip()}")

    allowed_prefixes = {
        "AGENTS.md:",
        "CLAUDE.md:",
        "docs/architecture/release_isolation_policy.md:",
        "runtime_data/README.md:",
        "tools/release/release_isolation_gate.py:",
    }

    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    unexpected = [line for line in lines if not any(line.startswith(prefix) for prefix in allowed_prefixes)]
    if unexpected:
        sample = "\n".join(unexpected[:20])
        return CheckResult("legacy_path_refs", False, f"unexpected legacy references:\n{sample}")
    return CheckResult("legacy_path_refs", True, "legacy evidence references migrated")


def check_no_private_assets_in_registry(root: Path) -> CheckResult:
    cmd = [
        "rg",
        "-n",
        "runtime_data/private-assets",
        "shared/registry",
        "config/openclaw.phase05.fragment.json",
        "config/openclaw.phase05.with-entry.fragment.json",
    ]
    proc = run(cmd, root)
    if proc.returncode == 1:
        return CheckResult("private_assets_registry_leak", True, "no private asset paths in registry/config fragments")
    if proc.returncode == 0:
        return CheckResult("private_assets_registry_leak", False, proc.stdout.strip())
    return CheckResult("private_assets_registry_leak", False, f"rg failed: {proc.stderr.strip()}")


def check_registry_verify(root: Path) -> CheckResult:
    cmd = ["python3", "shared/registry/registry_contract_tool.py", "verify"]
    proc = run(cmd, root)
    if proc.returncode != 0:
        detail = proc.stdout.strip() or proc.stderr.strip() or "registry verify failed"
        return CheckResult("registry_verify", False, detail)
    return CheckResult("registry_verify", True, (proc.stdout.strip() or "verify passed"))


def check_release_whitelist(root: Path) -> CheckResult:
    cmd = ["python3", "tools/release/generate_release_whitelist.py", "--strict"]
    proc = run(cmd, root)
    if proc.returncode != 0:
        detail = proc.stdout.strip() or proc.stderr.strip() or "release whitelist strict generation failed"
        return CheckResult("release_whitelist", False, detail)
    return CheckResult("release_whitelist", True, proc.stdout.strip() or "release whitelist generated")


def check_openclaw_scope_switch(root: Path) -> CheckResult:
    checks = []
    for scope in ("public", "dev"):
        cmd = [
            "python3",
            "tools/openclaw/switch_workspace.py",
            "--repo-root",
            str(root),
            "--scope",
            scope,
            "--dry-run",
        ]
        proc = run(cmd, root)
        checks.append((scope, proc.returncode, proc.stderr.strip(), proc.stdout.strip()))
        if proc.returncode != 0:
            return CheckResult(
                "openclaw_scope_switch",
                False,
                f"scope={scope} dry-run failed: {(proc.stderr.strip() or proc.stdout.strip())[:800]}",
            )
    return CheckResult("openclaw_scope_switch", True, "public/dev dry-run switch passed")


def check_openclaw_health(root: Path) -> CheckResult:
    cmd = ["openclaw", "health", "--json"]
    proc = run(cmd, root)
    if proc.returncode != 0:
        return CheckResult("openclaw_health", False, proc.stderr.strip() or "openclaw health failed")
    if '"ok": true' not in proc.stdout:
        return CheckResult("openclaw_health", False, "openclaw health returned non-ok payload")
    return CheckResult("openclaw_health", True, "openclaw health ok")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ANC v2 release isolation gate")
    parser.add_argument(
        "--verify-openclaw",
        action="store_true",
        help="Run OpenClaw runtime checks (health + scope dry-run switch).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    results = [
        check_public_evidence_placeholder(root),
        check_legacy_path_refs(root),
        check_no_private_assets_in_registry(root),
        check_release_whitelist(root),
        check_registry_verify(root),
    ]

    if args.verify_openclaw:
        results.append(check_openclaw_health(root))
        results.append(check_openclaw_scope_switch(root))

    passed = all(item.passed for item in results)
    report = {
        "passed": passed,
        "results": [
            {
                "name": item.name,
                "passed": item.passed,
                "detail": item.detail,
            }
            for item in results
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if not passed:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
