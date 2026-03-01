#!/usr/bin/env python3
"""Append and verify M6 round evidence JSONL events."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


ROUND_ID_RE = re.compile(r"^R-\d{8}-M6-[a-z0-9-]+-\d{2}$")
EVENT_TYPES = {"round_open", "checkpoint_synced", "round_close"}
SYNC_STATUS = {"in_sync", "needs_sync", "conflict", "blocked"}


class RoundEvidenceError(RuntimeError):
    """Fail-closed error type."""


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
        raise RoundEvidenceError("Not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def append_event(log_path: Path, event: Dict[str, Any]) -> None:
    ensure_parent(log_path)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def load_events(log_path: Path) -> List[Dict[str, Any]]:
    if not log_path.exists():
        raise RoundEvidenceError(f"round evidence log missing: {log_path}")

    events: List[Dict[str, Any]] = []
    for lineno, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RoundEvidenceError(f"invalid JSONL at line {lineno}: {exc}") from exc
        if not isinstance(parsed, dict):
            raise RoundEvidenceError(f"line {lineno} is not object")
        events.append(parsed)
    return events


def require_fields(event: Dict[str, Any], fields: List[str], idx: int, errors: List[str]) -> None:
    for field in fields:
        if field not in event:
            errors.append(f"event[{idx}] missing field: {field}")


def validate_event_shape(events: List[Dict[str, Any]]) -> List[str]:
    errors: List[str] = []
    for idx, event in enumerate(events):
        event_name = event.get("event")
        if event_name not in EVENT_TYPES:
            errors.append(f"event[{idx}] invalid event type: {event_name!r}")
            continue

        require_fields(event, ["event", "round_id", "superpower_ref", "ts"], idx, errors)

        round_id = event.get("round_id")
        if not isinstance(round_id, str) or ROUND_ID_RE.match(round_id) is None:
            errors.append(f"event[{idx}] invalid round_id: {round_id!r}")

        superpower_ref = event.get("superpower_ref")
        if not isinstance(superpower_ref, str) or not superpower_ref.strip():
            errors.append(f"event[{idx}] superpower_ref must be non-empty string")

        if event_name == "round_open":
            require_fields(event, ["round_goal", "owner"], idx, errors)
        elif event_name == "checkpoint_synced":
            require_fields(
                event,
                ["entire_checkpoint_id", "commit_sha", "changed_files", "sync_status"],
                idx,
                errors,
            )
            if event.get("sync_status") not in SYNC_STATUS:
                errors.append(f"event[{idx}] invalid sync_status: {event.get('sync_status')!r}")
            changed_files = event.get("changed_files")
            if not isinstance(changed_files, list) or not all(isinstance(x, str) for x in changed_files):
                errors.append(f"event[{idx}] changed_files must be list[str]")
        elif event_name == "round_close":
            require_fields(
                event,
                [
                    "decision_snapshot_ref",
                    "final_sync_status",
                    "checkpoint_count",
                    "commit_count",
                    "verdict",
                ],
                idx,
                errors,
            )
            if event.get("final_sync_status") not in SYNC_STATUS:
                errors.append(
                    f"event[{idx}] invalid final_sync_status: {event.get('final_sync_status')!r}"
                )
            if not isinstance(event.get("checkpoint_count"), int):
                errors.append(f"event[{idx}] checkpoint_count must be int")
            if not isinstance(event.get("commit_count"), int):
                errors.append(f"event[{idx}] commit_count must be int")
    return errors


def parse_git_commits(root: Path, git_range: str) -> List[Dict[str, Any]]:
    proc = subprocess.run(
        ["git", "log", "--name-only", "--pretty=format:__COMMIT__%n%H%n%B", git_range],
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RoundEvidenceError(f"git log failed for range {git_range!r}: {proc.stderr.strip()}")

    chunks = proc.stdout.split("__COMMIT__\n")
    commits: List[Dict[str, Any]] = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        lines = chunk.splitlines()
        sha = lines[0].strip() if lines else ""
        message_lines: List[str] = []
        changed_files: List[str] = []
        in_files = False
        for line in lines[1:]:
            if line.strip() == "":
                in_files = True
                continue
            if not in_files:
                message_lines.append(line)
            else:
                changed_files.append(line.strip())
        commits.append(
            {
                "sha": sha,
                "message": "\n".join(message_lines).strip(),
                "changed_files": [x for x in changed_files if x],
            }
        )
    return commits


def validate_sequence(
    root: Path,
    events: List[Dict[str, Any]],
    git_range: Optional[str],
) -> Dict[str, Any]:
    errors = validate_event_shape(events)
    warnings: List[str] = []

    if not events:
        errors.append("round evidence log is empty")
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "summary": {},
        }

    counts = Counter(event["event"] for event in events if isinstance(event.get("event"), str))
    if counts.get("round_open", 0) != 1:
        errors.append("round_open must appear exactly once")
    if counts.get("round_close", 0) != 1:
        errors.append("round_close must appear exactly once")

    if events[0].get("event") != "round_open":
        errors.append("round_open must be first event")
    if events[-1].get("event") != "round_close":
        errors.append("round_close must be last event")

    for idx, event in enumerate(events[1:-1], start=1):
        if event.get("event") != "checkpoint_synced":
            errors.append(f"event[{idx}] only checkpoint_synced allowed between open/close")

    round_ids = {event.get("round_id") for event in events}
    if len(round_ids) != 1:
        errors.append(f"single round_id required, found: {sorted(round_ids)}")

    superpower_refs = {event.get("superpower_ref") for event in events}
    if len(superpower_refs) != 1:
        errors.append(f"single superpower_ref required, found: {sorted(superpower_refs)}")

    checkpoint_events = [e for e in events if e.get("event") == "checkpoint_synced"]
    close_event = next((e for e in events if e.get("event") == "round_close"), None)
    if close_event:
        cp_count = close_event.get("checkpoint_count")
        cm_count = close_event.get("commit_count")
        if isinstance(cp_count, int) and isinstance(cm_count, int):
            if cp_count != cm_count:
                errors.append("round_close checkpoint_count must equal commit_count")
            if cp_count != len(checkpoint_events):
                errors.append(
                    f"round_close checkpoint_count {cp_count} does not match checkpoint events {len(checkpoint_events)}"
                )

    git_commit_count = None
    if git_range:
        commits = parse_git_commits(root, git_range)
        git_commit_count = len(commits)
        for commit in commits:
            if "Entire-Checkpoint:" not in commit["message"]:
                errors.append(f"commit missing Entire-Checkpoint trailer: {commit['sha']}")
        if close_event and isinstance(close_event.get("commit_count"), int):
            if close_event["commit_count"] != git_commit_count:
                errors.append(
                    f"round_close commit_count {close_event['commit_count']} does not match git range commits {git_commit_count}"
                )
        if not commits:
            warnings.append(f"git range {git_range!r} has no commits")

    summary = {
        "round_id": next(iter(round_ids)) if round_ids else None,
        "superpower_ref": next(iter(superpower_refs)) if superpower_refs else None,
        "event_count": len(events),
        "checkpoint_events": len(checkpoint_events),
        "git_commit_count": git_commit_count,
    }

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def cmd_open(args: argparse.Namespace, root: Path) -> int:
    event = {
        "event": "round_open",
        "round_id": args.round_id,
        "superpower_ref": args.superpower_ref,
        "round_goal": args.round_goal,
        "owner": args.owner,
        "ts": args.ts or now_iso(),
    }
    append_event(Path(args.log), event)
    print(json.dumps(event, ensure_ascii=False))
    return 0


def cmd_checkpoint(args: argparse.Namespace, root: Path) -> int:
    changed_files = args.changed_file or []
    event = {
        "event": "checkpoint_synced",
        "round_id": args.round_id,
        "superpower_ref": args.superpower_ref,
        "entire_checkpoint_id": args.checkpoint_id,
        "commit_sha": args.commit_sha,
        "changed_files": changed_files,
        "sync_status": args.sync_status,
        "ts": args.ts or now_iso(),
    }
    append_event(Path(args.log), event)
    print(json.dumps(event, ensure_ascii=False))
    return 0


def cmd_close(args: argparse.Namespace, root: Path) -> int:
    event = {
        "event": "round_close",
        "round_id": args.round_id,
        "superpower_ref": args.superpower_ref,
        "decision_snapshot_ref": args.decision_snapshot_ref,
        "final_sync_status": args.final_sync_status,
        "checkpoint_count": args.checkpoint_count,
        "commit_count": args.commit_count,
        "verdict": args.verdict,
        "ts": args.ts or now_iso(),
    }
    append_event(Path(args.log), event)
    print(json.dumps(event, ensure_ascii=False))
    return 0


def cmd_verify(args: argparse.Namespace, root: Path) -> int:
    result = validate_sequence(root, load_events(Path(args.log)), git_range=args.git_range)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"valid={str(result['valid']).lower()}")
        for warning in result["warnings"]:
            print(f"WARN: {warning}")
        for err in result["errors"]:
            print(f"ERROR: {err}")
        if result.get("summary"):
            for key, value in result["summary"].items():
                print(f"{key}={value}")
    return 0 if result["valid"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Round evidence JSONL tool")
    sub = parser.add_subparsers(dest="command", required=True)

    p_open = sub.add_parser("open", help="append round_open event")
    p_open.add_argument("--log", required=True)
    p_open.add_argument("--round-id", required=True)
    p_open.add_argument("--superpower-ref", required=True)
    p_open.add_argument("--round-goal", required=True)
    p_open.add_argument("--owner", required=True)
    p_open.add_argument("--ts", default=None)
    p_open.set_defaults(func=cmd_open)

    p_checkpoint = sub.add_parser("checkpoint", help="append checkpoint_synced event")
    p_checkpoint.add_argument("--log", required=True)
    p_checkpoint.add_argument("--round-id", required=True)
    p_checkpoint.add_argument("--superpower-ref", required=True)
    p_checkpoint.add_argument("--checkpoint-id", required=True)
    p_checkpoint.add_argument("--commit-sha", required=True)
    p_checkpoint.add_argument("--changed-file", action="append", default=[])
    p_checkpoint.add_argument("--sync-status", required=True, choices=sorted(SYNC_STATUS))
    p_checkpoint.add_argument("--ts", default=None)
    p_checkpoint.set_defaults(func=cmd_checkpoint)

    p_close = sub.add_parser("close", help="append round_close event")
    p_close.add_argument("--log", required=True)
    p_close.add_argument("--round-id", required=True)
    p_close.add_argument("--superpower-ref", required=True)
    p_close.add_argument("--decision-snapshot-ref", required=True)
    p_close.add_argument("--final-sync-status", required=True, choices=sorted(SYNC_STATUS))
    p_close.add_argument("--checkpoint-count", required=True, type=int)
    p_close.add_argument("--commit-count", required=True, type=int)
    p_close.add_argument("--verdict", required=True)
    p_close.add_argument("--ts", default=None)
    p_close.set_defaults(func=cmd_close)

    p_verify = sub.add_parser("verify", help="verify round evidence JSONL")
    p_verify.add_argument("--log", required=True)
    p_verify.add_argument("--git-range", default=None)
    p_verify.add_argument("--json", action="store_true")
    p_verify.set_defaults(func=cmd_verify)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        root = repo_root()
        return args.func(args, root)
    except RoundEvidenceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
