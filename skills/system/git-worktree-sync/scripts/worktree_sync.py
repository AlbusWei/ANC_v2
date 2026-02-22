#!/usr/bin/env python3
"""Sync a parent branch with source branch and fan out to sibling worktrees."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


class SyncError(RuntimeError):
    """Fail-closed runtime error."""


@dataclass
class WorktreeInfo:
    path: Path
    branch: Optional[str]
    detached: bool


def run_cmd(cmd: Sequence[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        list(cmd),
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and proc.returncode != 0:
        rendered = " ".join(shlex.quote(part) for part in cmd)
        location = str(cwd) if cwd else "."
        raise SyncError(
            f"command failed ({location}): {rendered}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )
    return proc


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run_cmd(["git", *args], cwd=cwd, check=check)


def repo_root() -> Path:
    proc = run_cmd(["git", "rev-parse", "--show-toplevel"], check=False)
    if proc.returncode != 0:
        raise SyncError("not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def list_worktrees(root: Path) -> List[WorktreeInfo]:
    proc = git(root, "worktree", "list", "--porcelain")
    blocks = proc.stdout.strip().split("\n\n")
    out: List[WorktreeInfo] = []
    for block in blocks:
        if not block.strip():
            continue
        path: Optional[Path] = None
        branch: Optional[str] = None
        detached = False
        for line in block.splitlines():
            if line.startswith("worktree "):
                path = Path(line[len("worktree ") :].strip()).resolve()
            elif line.startswith("branch refs/heads/"):
                branch = line[len("branch refs/heads/") :].strip()
            elif line.strip() == "detached":
                detached = True
        if path is None:
            raise SyncError(f"invalid worktree block: {block!r}")
        out.append(WorktreeInfo(path=path, branch=branch, detached=detached))
    return out


def worktree_by_branch(worktrees: List[WorktreeInfo]) -> Dict[str, Path]:
    mapping: Dict[str, Path] = {}
    for wt in worktrees:
        if wt.branch:
            mapping[wt.branch] = wt.path
    return mapping


def ensure_branch_exists(root: Path, branch: str) -> None:
    proc = git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False)
    if proc.returncode != 0:
        raise SyncError(f"local branch does not exist: {branch}")


def ensure_remote_branch_exists(root: Path, remote: str, branch: str) -> None:
    proc = git(root, "show-ref", "--verify", "--quiet", f"refs/remotes/{remote}/{branch}", check=False)
    if proc.returncode != 0:
        raise SyncError(f"remote branch does not exist: {remote}/{branch}")


def current_branch(path: Path) -> str:
    proc = git(path, "rev-parse", "--abbrev-ref", "HEAD")
    branch = proc.stdout.strip()
    if branch == "HEAD":
        raise SyncError(f"detached HEAD is not supported in {path}")
    return branch


def dirty_stats(path: Path) -> Tuple[int, int]:
    status = git(path, "status", "--porcelain")
    dirty_files = len([line for line in status.stdout.splitlines() if line.strip()])

    def _count_lines(shortstat: str) -> int:
        insertions = re.search(r"(\d+) insertions?\(\+\)", shortstat)
        deletions = re.search(r"(\d+) deletions?\(-\)", shortstat)
        total = 0
        if insertions:
            total += int(insertions.group(1))
        if deletions:
            total += int(deletions.group(1))
        return total

    unstaged = git(path, "diff", "--shortstat").stdout
    staged = git(path, "diff", "--cached", "--shortstat").stdout
    dirty_lines = _count_lines(unstaged) + _count_lines(staged)
    return dirty_files, dirty_lines


def ensure_clean(path: Path, label: str) -> None:
    files, lines = dirty_stats(path)
    if files > 0:
        raise SyncError(f"{label} is not clean: {files} file(s), {lines} line(s) changed")


def exec_mutating(path: Path, apply: bool, *args: str) -> subprocess.CompletedProcess[str]:
    rendered = " ".join(shlex.quote(part) for part in ("git", *args))
    if not apply:
        print(f"[dry-run] ({path}) {rendered}")
        return subprocess.CompletedProcess(["git", *args], 0, "", "")
    return git(path, *args, check=False)


def merge_abort_if_needed(path: Path) -> None:
    check_merge_head = git(path, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False)
    if check_merge_head.returncode == 0:
        git(path, "merge", "--abort", check=False)


def run_test_command(path: Path, test_cmd: str, apply: bool) -> int:
    if not test_cmd:
        return 0
    if not apply:
        print(f"[dry-run] ({path}) bash -lc {shlex.quote(test_cmd)}")
        return 0
    proc = subprocess.run(
        ["bash", "-lc", test_cmd],
        cwd=str(path),
        check=False,
    )
    return proc.returncode


def cmd_integrate(args: argparse.Namespace) -> int:
    root = repo_root()
    if args.source == args.parent:
        raise SyncError("source and parent cannot be the same branch")

    ensure_branch_exists(root, args.source)
    ensure_branch_exists(root, args.parent)

    worktrees = list_worktrees(root)
    mapping = worktree_by_branch(worktrees)

    parent_path = mapping.get(args.parent)
    if parent_path is None:
        raise SyncError(f"parent branch must be checked out in a worktree: {args.parent}")

    source_path = mapping.get(args.source)
    if source_path:
        ensure_clean(source_path, f"source worktree {args.source}")

    ensure_clean(parent_path, f"parent worktree {args.parent}")
    if current_branch(parent_path) != args.parent:
        raise SyncError(f"parent worktree path is not on branch {args.parent}: {parent_path}")

    git(root, "fetch", args.remote)
    ensure_remote_branch_exists(root, args.remote, args.parent)

    summary: Dict[str, object] = {
        "mode": "integrate",
        "source": args.source,
        "parent": args.parent,
        "parent_worktree": str(parent_path),
        "dry_run": not args.apply,
        "steps": [],
    }
    steps: List[Dict[str, str]] = summary["steps"]  # type: ignore[assignment]

    ff_proc = exec_mutating(parent_path, args.apply, "merge", "--ff-only", f"{args.remote}/{args.parent}")
    if ff_proc.returncode != 0:
        raise SyncError(
            f"cannot fast-forward parent {args.parent} to {args.remote}/{args.parent}; "
            "resolve divergence manually first"
        )
    steps.append({"name": "ff_parent_from_remote", "status": "ok"})

    merge_proc = exec_mutating(parent_path, args.apply, "merge", "--no-ff", "--no-edit", args.source)
    if merge_proc.returncode != 0:
        merge_abort_if_needed(parent_path)
        steps.append({"name": "merge_source_into_parent", "status": "manual_conflict"})
        summary["result"] = "manual_conflict"
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 4
    steps.append({"name": "merge_source_into_parent", "status": "ok"})

    if args.test_cmd:
        test_rc = run_test_command(parent_path, args.test_cmd, args.apply)
        if test_rc != 0:
            steps.append({"name": "test_command", "status": "failed"})
            summary["result"] = "test_failed"
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 5
        steps.append({"name": "test_command", "status": "ok"})

    if args.push:
        push_proc = exec_mutating(parent_path, args.apply, "push", args.remote, args.parent)
        if push_proc.returncode != 0:
            raise SyncError(f"push failed for {args.parent}")
        steps.append({"name": "push_parent", "status": "ok"})

    summary["result"] = "ok"
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def resolve_branch_candidates(
    worktrees: List[WorktreeInfo],
    parent: str,
    source: Optional[str],
    explicit_siblings: Optional[str],
    exclude_csv: Optional[str],
) -> List[Tuple[str, Path]]:
    mapping = worktree_by_branch(worktrees)

    excludes = {parent}
    if source:
        excludes.add(source)
    if exclude_csv:
        excludes.update({item.strip() for item in exclude_csv.split(",") if item.strip()})

    if explicit_siblings:
        selected = [item.strip() for item in explicit_siblings.split(",") if item.strip()]
        out: List[Tuple[str, Path]] = []
        for branch in selected:
            if branch in excludes:
                continue
            path = mapping.get(branch)
            if path is None:
                raise SyncError(f"sibling branch not checked out in a worktree: {branch}")
            out.append((branch, path))
        return out

    out = []
    for wt in worktrees:
        if wt.detached or not wt.branch:
            continue
        if wt.branch in excludes:
            continue
        out.append((wt.branch, wt.path))
    return out


def fetch_upstream_ref(path: Path, remote: str, branch: str) -> Optional[str]:
    upstream = git(path, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", check=False)
    if upstream.returncode == 0:
        return upstream.stdout.strip()
    remote_ref = f"{remote}/{branch}"
    probe = git(path, "show-ref", "--verify", "--quiet", f"refs/remotes/{remote_ref}", check=False)
    if probe.returncode == 0:
        return remote_ref
    return None


def maybe_stash(path: Path, apply: bool, reason: str) -> bool:
    if not apply:
        print(f"[dry-run] ({path}) git stash push -u -m {shlex.quote(reason)}")
        return True
    proc = git(path, "stash", "push", "-u", "-m", reason)
    return "No local changes to save" not in proc.stdout


def maybe_pop_stash(path: Path, apply: bool) -> bool:
    if not apply:
        print(f"[dry-run] ({path}) git stash pop")
        return True
    proc = git(path, "stash", "pop", check=False)
    return proc.returncode == 0


def sync_one_sibling(path: Path, branch: str, args: argparse.Namespace) -> Dict[str, object]:
    result: Dict[str, object] = {
        "branch": branch,
        "worktree": str(path),
        "status": "unknown",
        "details": [],
    }
    details: List[str] = result["details"]  # type: ignore[assignment]

    if current_branch(path) != branch:
        result["status"] = "error"
        details.append("worktree branch mismatch")
        return result

    dirty_files, dirty_lines = dirty_stats(path)
    stashed = False
    if dirty_files > 0:
        if dirty_files > args.max_dirty_files or dirty_lines > args.max_dirty_lines:
            result["status"] = "skipped"
            details.append(
                f"dirty changes exceed threshold ({dirty_files} files, {dirty_lines} lines; "
                f"limits {args.max_dirty_files}/{args.max_dirty_lines})"
            )
            return result
        if not args.allow_dirty_stash:
            result["status"] = "skipped"
            details.append("dirty worktree and stash disabled")
            return result
        stashed = maybe_stash(path, args.apply, f"git-worktree-sync/{branch}")
        details.append("stashed local changes")

    upstream = fetch_upstream_ref(path, args.remote, branch)
    if upstream:
        ff_proc = exec_mutating(path, args.apply, "merge", "--ff-only", upstream)
        if ff_proc.returncode != 0:
            result["status"] = "manual_required"
            details.append(f"cannot fast-forward from upstream {upstream}")
            if stashed:
                maybe_pop_stash(path, args.apply)
            return result
        details.append(f"fast-forwarded from {upstream}")

    merge_proc = exec_mutating(path, args.apply, "merge", "--no-ff", "--no-edit", args.parent)
    if merge_proc.returncode != 0:
        merge_abort_if_needed(path)
        result["status"] = "manual_conflict"
        details.append(f"conflict while merging parent {args.parent}")
        if stashed:
            maybe_pop_stash(path, args.apply)
        return result
    details.append(f"merged parent {args.parent}")

    if args.push:
        push_proc = exec_mutating(path, args.apply, "push", args.remote, branch)
        if push_proc.returncode != 0:
            result["status"] = "manual_required"
            details.append("push failed")
            if stashed:
                maybe_pop_stash(path, args.apply)
            return result
        details.append("pushed branch")

    if stashed:
        popped = maybe_pop_stash(path, args.apply)
        if not popped:
            result["status"] = "manual_conflict"
            details.append("conflict while applying stashed changes")
            return result
        details.append("reapplied stashed changes")

    result["status"] = "ok"
    return result


def cmd_fanout(args: argparse.Namespace) -> int:
    root = repo_root()
    ensure_branch_exists(root, args.parent)
    git(root, "fetch", args.remote)
    ensure_remote_branch_exists(root, args.remote, args.parent)

    worktrees = list_worktrees(root)
    candidates = resolve_branch_candidates(
        worktrees=worktrees,
        parent=args.parent,
        source=args.source,
        explicit_siblings=args.siblings,
        exclude_csv=args.exclude,
    )

    report: Dict[str, object] = {
        "mode": "fanout",
        "parent": args.parent,
        "dry_run": not args.apply,
        "results": [],
    }
    results: List[Dict[str, object]] = report["results"]  # type: ignore[assignment]

    for branch, path in candidates:
        results.append(sync_one_sibling(path, branch, args))

    blocking = [
        item for item in results if item["status"] in {"manual_required", "manual_conflict", "error"}
    ]
    report["summary"] = {
        "total": len(results),
        "ok": len([item for item in results if item["status"] == "ok"]),
        "skipped": len([item for item in results if item["status"] == "skipped"]),
        "manual_required": len(blocking),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 4 if blocking else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync source->parent and parent->siblings across git worktrees")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    integrate = subparsers.add_parser("integrate", help="Merge source branch into parent branch")
    integrate.add_argument("--source", required=True, help="Source branch that has finished changes")
    integrate.add_argument("--parent", required=True, help="Parent branch to receive source changes")
    integrate.add_argument("--remote", default="origin", help="Remote name (default: origin)")
    integrate.add_argument("--test-cmd", default="", help="Optional test command in parent worktree")
    integrate.add_argument("--push", action="store_true", help="Push parent branch after merge")
    integrate.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")
    integrate.set_defaults(func=cmd_integrate)

    fanout = subparsers.add_parser("fanout", help="Merge parent branch into sibling worktrees")
    fanout.add_argument("--parent", required=True, help="Parent branch with latest integrated changes")
    fanout.add_argument("--source", default="", help="Optional source branch to exclude from siblings")
    fanout.add_argument("--siblings", default="", help="Optional comma-separated sibling branches")
    fanout.add_argument("--exclude", default="", help="Optional comma-separated excluded branches")
    fanout.add_argument("--remote", default="origin", help="Remote name (default: origin)")
    fanout.add_argument("--max-dirty-files", type=int, default=5, help="Skip branch when dirty file count exceeds this value")
    fanout.add_argument("--max-dirty-lines", type=int, default=200, help="Skip branch when dirty line count exceeds this value")
    fanout.add_argument(
        "--allow-dirty-stash",
        action="store_true",
        default=False,
        help="Allow small dirty changes by auto-stashing before merge",
    )
    fanout.add_argument("--push", action="store_true", help="Push each sibling branch after merge")
    fanout.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")
    fanout.set_defaults(func=cmd_fanout)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except SyncError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
