#!/usr/bin/env python3
"""M2 post-dev live regression 执行器。

Fail-Closed 约束：
1. git-range/checkpoint-map/case-manifest 等前置文件必须存在且可解析。
2. git-range 内每个提交都必须包含 Entire-Checkpoint trailer。
3. git-range 内每个提交都必须能在 checkpoint_commit_map.jsonl 对账。
4. 若 git_range.txt 含 round_dir，则提交数必须等于 round_close.commit_count。
5. Online + W1/W2/W3/W3-B/W5 套件必须在 live 模式全部通过。
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


@dataclass
class SuiteExecution:
    suite_id: str
    command: str
    return_code: int
    status: str
    report_ref: str
    summary: Dict[str, Any]
    stderr_tail: str


@dataclass
class RegressionResult:
    status: str
    mode: str
    checked_files: List[str]
    errors: List[str]
    suites: List[Dict[str, Any]]
    ts: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_json_from_mixed_output(text: str) -> Any:
    decoder = json.JSONDecoder()
    fallback: Any = None
    for idx, ch in enumerate(text):
        if ch not in "[{":
            continue
        try:
            value, end = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        remainder = text[idx + end :].strip()
        if not remainder:
            return value
        fallback = value
    if fallback is not None:
        return fallback

    for line in reversed(text.splitlines()):
        raw = line.strip()
        if not raw:
            continue
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            continue
    return {}


def parse_git_range(path: Path, errors: List[str]) -> Dict[str, str]:
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
    return values


def validate_git_range(path: Path, errors: List[str]) -> Dict[str, str]:
    values = parse_git_range(path, errors)
    required_keys = ("base_commit", "head_commit", "range")
    for key in required_keys:
        if not values.get(key):
            errors.append(f"missing_git_range_key:{path}:{key}")

    range_value = values.get("range", "")
    if range_value and ".." not in range_value:
        errors.append(f"invalid_git_range_format:{path}")
    return values


def validate_checkpoint_map(path: Path, errors: List[str]) -> Tuple[List[Dict[str, Any]], set[str]]:
    required_fields = {"round_id", "entire_checkpoint_id", "commit_sha", "changed_files", "ts"}
    line_count = 0
    records: List[Dict[str, Any]] = []
    commit_set: set[str] = set()
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
            continue
        commit_sha = payload.get("commit_sha")
        if not isinstance(commit_sha, str) or not commit_sha.strip():
            errors.append(f"invalid_commit_sha:{path}:{idx}")
            continue
        records.append(payload)
        commit_set.add(commit_sha.strip())

    if line_count == 0:
        errors.append(f"empty_checkpoint_map:{path}")
    return records, commit_set


def collect_git_commits(repo_root: Path, git_range: str, errors: List[str]) -> List[Tuple[str, str]]:
    proc = subprocess.run(
        ["git", "log", "--format=%H%n%B%n__END_COMMIT__", git_range],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        errors.append(f"git_log_failed:{git_range}:{proc.stderr.strip()}")
        return []

    commits: List[Tuple[str, str]] = []
    for block in proc.stdout.split("__END_COMMIT__"):
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        sha = lines[0].strip()
        message = "\n".join(lines[1:]).strip()
        commits.append((sha, message))
    return commits


def load_round_close_commit_count(round_dir: Path, errors: List[str]) -> int | None:
    evidence = round_dir / "round-evidence.jsonl"
    if not evidence.exists():
        errors.append(f"round_evidence_missing:{evidence}")
        return None
    close_count: int | None = None
    for idx, line in enumerate(evidence.read_text(encoding="utf-8").splitlines(), start=1):
        raw = line.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            errors.append(f"invalid_round_evidence_jsonl:{evidence}:{idx}")
            continue
        if payload.get("event") == "round_close":
            count = payload.get("commit_count")
            if isinstance(count, int):
                close_count = count
            else:
                errors.append(f"round_close_commit_count_invalid:{evidence}:{idx}")
    return close_count


def run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def _summary_failed(summary: Dict[str, Any]) -> bool:
    if not isinstance(summary, dict):
        return True
    if isinstance(summary.get("failed"), int):
        return summary["failed"] > 0
    status = str(summary.get("status", "")).strip().lower()
    if status in {"fail", "failed"}:
        return True
    return False


def execute_suite(
    repo_root: Path,
    suite_id: str,
    cmd: List[str],
    report_ref: str,
) -> SuiteExecution:
    proc = run_cmd(cmd, repo_root)
    summary = parse_json_from_mixed_output(proc.stdout)
    summary_obj = summary if isinstance(summary, dict) else {}
    failed = proc.returncode != 0 or _summary_failed(summary_obj)
    status = "failed" if failed else "passed"
    stderr_lines = [line for line in proc.stderr.splitlines() if line.strip()]
    stderr_tail = "\n".join(stderr_lines[-20:])
    return SuiteExecution(
        suite_id=suite_id,
        command=" ".join(shlex.quote(item) for item in cmd),
        return_code=proc.returncode,
        status=status,
        report_ref=report_ref,
        summary=summary_obj,
        stderr_tail=stderr_tail,
    )


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
    online_case_doc = repo_root / "tests/m2-bpm-runtime/TC-ONLINE.md"
    live_root_rel = Path("docs/design/modules/evidence/bpm-runtime/live-regression/latest")
    live_root = (repo_root / live_root_rel).resolve()

    required = [
        repo_root / "docs/design/modules/evidence/bpm-runtime/m6_live_regression_plan.md",
        map_file,
        git_range_file,
        case_manifest,
        online_case_doc,
    ]

    errors: List[str] = []
    for path in required:
        if not path.exists():
            errors.append(f"missing_required_file:{path}")

    git_values: Dict[str, str] = {}
    map_records: List[Dict[str, Any]] = []
    map_commit_set: set[str] = set()
    if not errors:
        git_values = validate_git_range(git_range_file, errors)
        map_records, map_commit_set = validate_checkpoint_map(map_file, errors)
        git_range = git_values.get("range", "")
        if git_range:
            commits = collect_git_commits(repo_root, git_range, errors)
            for sha, message in commits:
                if re.search(r"^Entire-Checkpoint:\s+\S+", message, flags=re.MULTILINE) is None:
                    errors.append(f"missing_entire_trailer:{sha}")
                if sha not in map_commit_set:
                    errors.append(f"missing_checkpoint_map_record:{sha}")

            round_dir_value = git_values.get("round_dir", "").strip()
            if round_dir_value:
                round_dir = (repo_root / round_dir_value).resolve()
                if not round_dir.exists() or not round_dir.is_dir():
                    errors.append(f"round_dir_not_found:{round_dir}")
                else:
                    close_commit_count = load_round_close_commit_count(round_dir, errors)
                    if isinstance(close_commit_count, int) and close_commit_count != len(commits):
                        errors.append(
                            f"round_close_commit_count_mismatch:{close_commit_count}!={len(commits)}"
                        )

    suite_execs: List[SuiteExecution] = []
    suite_reports: List[Path] = []
    if not errors:
        live_root.mkdir(parents=True, exist_ok=True)
        suite_plan = [
            (
                "TC-ONLINE",
                [
                    "python3",
                    "tests/m2-bpm-runtime/run_tc_online.py",
                    "--report",
                    str((live_root_rel / "w0_tc_online_report.json").as_posix()),
                ],
                live_root / "w0_tc_online_report.json",
            ),
            (
                "TC-INS",
                [
                    "python3",
                    "tests/m2-bpm-runtime/run_tc_ins.py",
                    "--run-live-migration",
                    "--report",
                    str((live_root_rel / "w1_tc_ins_report.json").as_posix()),
                    "--migration-report",
                    str((live_root_rel / "w1_migration_report.json").as_posix()),
                    "--replay-report",
                    str((live_root_rel / "w1_replay_report.json").as_posix()),
                    "--sandbox-root",
                    "tmp/m2-bpm-runtime/live-regression/tc-ins-sandbox",
                ],
                live_root / "w1_tc_ins_report.json",
            ),
            (
                "TC-GCC",
                [
                    "python3",
                    "tests/m2-bpm-runtime/run_tc_gcc.py",
                    "--report",
                    str((live_root_rel / "w2_tc_gcc_report.json").as_posix()),
                    "--evidence-root",
                    str((live_root_rel / "w2_tc_gcc_cases").as_posix()),
                ],
                live_root / "w2_tc_gcc_report.json",
            ),
            (
                "TC-TG",
                [
                    "python3",
                    "tests/m2-bpm-runtime/run_tc_tg.py",
                    "--report",
                    str((live_root_rel / "w3_tc_tg_report.json").as_posix()),
                    "--evidence-root",
                    str((live_root_rel / "w3_trigger_runtime_cases").as_posix()),
                    "--sandbox-root",
                    "tmp/m2-bpm-runtime/live-regression/tc-tg-sandbox",
                    "--instance-root",
                    "tmp/m2-bpm-runtime/live-regression/tc-tg-sandbox/instances",
                ],
                live_root / "w3_tc_tg_report.json",
            ),
            (
                "TC-QA-PROC",
                [
                    "python3",
                    "tests/m2-bpm-runtime/run_tc_qa_proc.py",
                    "--report",
                    str((live_root_rel / "w3b_tc_qa_proc_report.json").as_posix()),
                    "--evidence-root",
                    str((live_root_rel / "w3b_qa_process_cases").as_posix()),
                ],
                live_root / "w3b_tc_qa_proc_report.json",
            ),
            (
                "TC-ANL",
                [
                    "python3",
                    "tests/m2-bpm-runtime/run_tc_anl.py",
                    "--report",
                    str((live_root_rel / "w5_tc_anl_report.json").as_posix()),
                    "--evidence-root",
                    str((live_root_rel / "w5_system_analyst_prod_cases").as_posix()),
                ],
                live_root / "w5_tc_anl_report.json",
            ),
        ]

        for suite_id, cmd, report_abs in suite_plan:
            suite_exec = execute_suite(repo_root, suite_id, cmd, report_abs.relative_to(repo_root).as_posix())
            suite_execs.append(suite_exec)
            suite_reports.append(report_abs)
            if suite_exec.status != "passed":
                errors.append(f"suite_failed:{suite_id}:rc={suite_exec.return_code}")

        for report_abs in suite_reports:
            if not report_abs.exists():
                errors.append(f"missing_suite_report:{report_abs}")

    result = RegressionResult(
        status="failed" if errors else "passed",
        mode=args.mode,
        checked_files=[
            str(p.relative_to(repo_root)) for p in (required + [p for p in suite_reports if p.exists()])
        ],
        errors=errors,
        suites=[asdict(item) for item in suite_execs],
        ts=utc_now_iso(),
    )

    output_path = repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(asdict(result), ensure_ascii=False))
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
