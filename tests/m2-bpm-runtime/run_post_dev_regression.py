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
    required = [
        repo_root / "docs/design/modules/evidence/bpm-runtime/m6_live_regression_plan.md",
        repo_root / "docs/design/modules/evidence/bpm-runtime/checkpoint_commit_map.jsonl",
        repo_root / "docs/design/modules/evidence/bpm-runtime/git_range.txt",
    ]

    errors: list[str] = []
    for path in required:
        if not path.exists():
            errors.append(f"missing_required_file:{path}")

    # Thread 0 scaffold: if no concrete regression cases are defined, stop here.
    case_manifest = repo_root / "tests/m2-bpm-runtime/live_regression_cases.md"
    if not case_manifest.exists():
        errors.append(f"missing_case_manifest:{case_manifest}")

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
