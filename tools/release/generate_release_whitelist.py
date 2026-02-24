#!/usr/bin/env python3
"""Generate release whitelist from tracked files under isolation policy."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class Item:
    path: str
    reason: str


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=False)


def repo_root() -> Path:
    proc = run(["git", "rev-parse", "--show-toplevel"], Path.cwd())
    if proc.returncode != 0:
        raise RuntimeError("not inside git repository")
    return Path(proc.stdout.strip()).resolve()


def load_partition(root: Path) -> Dict[str, object]:
    cfg_path = root / "config/release.partition.json"
    if not cfg_path.exists():
        raise RuntimeError("missing config/release.partition.json")
    try:
        payload = json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid config/release.partition.json: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("config/release.partition.json root must be object")
    return payload


def read_git_files(root: Path) -> List[str]:
    proc = run(["git", "ls-files"], root)
    if proc.returncode != 0:
        raise RuntimeError(f"git ls-files failed: {proc.stderr.strip()}")
    files = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return sorted(files)


def read_git_commit(root: Path) -> str:
    proc = run(["git", "rev-parse", "HEAD"], root)
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def classify_files(
    files: List[str],
    exclude_prefixes: List[str],
    exclude_exact: List[str],
) -> Tuple[List[str], List[Item]]:
    include: List[str] = []
    exclude: List[Item] = []

    prefix_rules = [(prefix, prefix.rstrip("/") + "/") for prefix in exclude_prefixes]
    exact_set = set(exclude_exact)

    for path in files:
        if path in exact_set:
            exclude.append(Item(path=path, reason=f"excluded_exact:{path}"))
            continue

        hit = None
        for raw_prefix, normalized_prefix in prefix_rules:
            if path == raw_prefix.rstrip("/") or path.startswith(normalized_prefix):
                hit = raw_prefix
                break
        if hit is not None:
            exclude.append(Item(path=path, reason=f"excluded_prefix:{hit}"))
            continue

        include.append(path)

    return include, exclude


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate release whitelist manifest")
    parser.add_argument(
        "--output-dir",
        default="",
        help="Output directory (default from config/release.partition.json release_whitelist.output_dir)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when tracked files are excluded by whitelist rules.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    cfg = load_partition(root)

    whitelist_cfg = cfg.get("release_whitelist") or {}
    if not isinstance(whitelist_cfg, dict):
        raise RuntimeError("release_whitelist must be object")

    output_dir_raw = args.output_dir or str(whitelist_cfg.get("output_dir") or "runtime_data/exports/release-whitelist/latest")
    output_dir = Path(output_dir_raw)
    if not output_dir.is_absolute():
        output_dir = (root / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    exclude_prefixes = whitelist_cfg.get("exclude_prefixes") or []
    exclude_exact = whitelist_cfg.get("exclude_exact") or []
    if not isinstance(exclude_prefixes, list) or not all(isinstance(item, str) and item.strip() for item in exclude_prefixes):
        raise RuntimeError("release_whitelist.exclude_prefixes must be non-empty string list")
    if not isinstance(exclude_exact, list) or not all(isinstance(item, str) and item.strip() for item in exclude_exact):
        raise RuntimeError("release_whitelist.exclude_exact must be string list")

    files = read_git_files(root)
    include, exclude = classify_files(files, exclude_prefixes, exclude_exact)

    manifest = {
        "generated_at": now_iso(),
        "repo_root": str(root),
        "head": read_git_commit(root),
        "policy_ref": "config/release.partition.json",
        "summary": {
            "tracked_files": len(files),
            "whitelisted_files": len(include),
            "excluded_tracked_files": len(exclude),
            "strict_mode": bool(args.strict),
        },
        "exclude_rules": {
            "prefixes": exclude_prefixes,
            "exact": exclude_exact,
        },
        "whitelist": include,
        "excluded": [{"path": item.path, "reason": item.reason} for item in exclude],
    }

    output_json = output_dir / "release_whitelist.json"
    output_txt = output_dir / "release_whitelist.txt"
    output_excluded = output_dir / "excluded_tracked_files.json"

    output_json.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_txt.write_text("\n".join(include) + ("\n" if include else ""), encoding="utf-8")
    output_excluded.write_text(
        json.dumps({"excluded": manifest["excluded"]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = {
        "ok": not (args.strict and len(exclude) > 0),
        "output_json": str(output_json.relative_to(root)),
        "output_txt": str(output_txt.relative_to(root)),
        "output_excluded": str(output_excluded.relative_to(root)),
        "summary": manifest["summary"],
    }
    if args.strict and exclude:
        result["error"] = "strict mode blocked: excluded tracked files exist"

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.strict and exclude:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
