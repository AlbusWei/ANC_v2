#!/usr/bin/env python3
"""Post-development regression runner scaffold for m2-bpm-runtime-hardening.

Thread 0 provides a fail-closed executable entrypoint.
Thread 6 should extend this script with real live-regression checks.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class RegressionResult:
    status: str
    mode: str
    checked_files: list[str]
    errors: list[str]
    ts: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_git_range(path: Path, errors: list[str]) -> None:
    content = path.read_text(encoding="utf-8")
    values: dict[str, str] = {}
    for idx, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if "=" not in line:
            errors.append(f"invalid_git_range_line:{path}:{idx}")
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

    required_keys = ("base_commit", "head_commit", "range")
    for key in required_keys:
        if not values.get(key):
            errors.append(f"missing_git_range_key:{path}:{key}")

    range_value = values.get("range", "")
    if range_value and ".." not in range_value:
        errors.append(f"invalid_git_range_format:{path}")


def validate_checkpoint_map(path: Path, errors: list[str]) -> None:
    required_fields = {"round_id", "entire_checkpoint_id", "commit_sha", "changed_files", "ts"}
    line_count = 0
    for idx, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        line_count += 1
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"invalid_jsonl:{path}:{idx}")
            continue

        missing = sorted(field for field in required_fields if field not in payload)
        if missing:
            errors.append(f"missing_map_fields:{path}:{idx}:{','.join(missing)}")

    if line_count == 0:
        errors.append(f"empty_checkpoint_map:{path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run post-dev regression for M2 BPM runtime hardening")
    parser.add_argument(
        "--mode",
        choices=("live",),
        default="live",
        help="Regression mode. Thread 6 requires live execution.",
    )
    parser.add_argument(
        "--output",
        default="docs/design/modules/evidence/bpm-runtime/latest_live_regression_result.json",
        help="Output JSON path for regression result.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    map_file = repo_root / "docs/design/modules/evidence/bpm-runtime/checkpoint_commit_map.jsonl"
    git_range_file = repo_root / "docs/design/modules/evidence/bpm-runtime/git_range.txt"
    case_manifest = repo_root / "tests/m2-bpm-runtime/live_regression_cases.md"

    required = [
        repo_root / "docs/design/modules/evidence/bpm-runtime/m6_live_regression_plan.md",
        map_file,
        git_range_file,
        case_manifest,
    ]

    errors: list[str] = []
    for path in required:
        if not path.exists():
            errors.append(f"missing_required_file:{path}")

    if not errors:
        validate_git_range(git_range_file, errors)
        validate_checkpoint_map(map_file, errors)

    result = RegressionResult(
        status="failed" if errors else "passed",
        mode=args.mode,
        checked_files=[str(p.relative_to(repo_root)) for p in required],
        errors=errors,
        ts=utc_now_iso(),
    )

    output_path = repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(result), ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(asdict(result), ensure_ascii=True))
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
