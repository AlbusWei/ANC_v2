#!/usr/bin/env python3
"""Runtime validation for system.ops.git-worktree-sync."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class CaseResult:
    case_id: str
    name: str
    passed: bool
    gate_decision: str
    reasons: List[str]
    return_code: int
    expected_return_code: int
    payload_ref: str
    stdout_ref: str
    stderr_ref: str


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "skills/system/git-worktree-sync/scripts/worktree_sync.py"
EVIDENCE_ROOT = REPO_ROOT / "tests/git-worktree-sync/evidence/runtime-validation-round-1"
RUN_OUTPUT_ROOT = EVIDENCE_ROOT / "outputs"
ENV_ROOT = EVIDENCE_ROOT / "tmp_env"


def run(cmd: List[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
    if check and completed.returncode != 0:
        rendered = " ".join(cmd)
        raise RuntimeError(
            f"command failed: {rendered}\n"
            f"cwd: {cwd}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return completed


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=cwd, check=check)


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_json_report(stdout: str) -> Dict[str, object]:
    idx = stdout.rfind("\n{")
    if idx >= 0:
        candidate = stdout[idx + 1 :].strip()
        return json.loads(candidate)
    stripped = stdout.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    raise ValueError("json_report_not_found")


def init_repo(case_dir: Path, with_mirror: bool = False) -> Tuple[Path, Path, Path]:
    origin_bare = case_dir / "origin.git"
    workspace = case_dir / "workspace"
    wt_rebuild = case_dir / "wt-rebuild"

    git(case_dir, "init", "--bare", str(origin_bare))
    git(case_dir, "init", str(workspace))

    git(workspace, "config", "user.name", "QA Bot")
    git(workspace, "config", "user.email", "qa-bot@example.com")

    (workspace / "README.md").write_text("runtime validation\n", encoding="utf-8")
    git(workspace, "add", "README.md")
    git(workspace, "commit", "-m", "init")
    git(workspace, "branch", "-M", "main")

    git(workspace, "remote", "add", "origin", str(origin_bare))
    git(workspace, "push", "-u", "origin", "main")

    git(workspace, "checkout", "-b", "rebuild")
    (workspace / "base.txt").write_text("base\n", encoding="utf-8")
    git(workspace, "add", "base.txt")
    git(workspace, "commit", "-m", "rebuild base")
    git(workspace, "push", "-u", "origin", "rebuild")

    if with_mirror:
        mirror_bare = case_dir / "mirror.git"
        git(case_dir, "init", "--bare", str(mirror_bare))
        git(workspace, "remote", "add", "mirror", str(mirror_bare))
    else:
        mirror_bare = Path("")

    git(workspace, "checkout", "main")
    git(workspace, "worktree", "add", str(wt_rebuild), "rebuild")
    return workspace, wt_rebuild, mirror_bare


def run_skill(cwd: Path, args: List[str]) -> Tuple[int, str, str, Dict[str, object]]:
    cmd = [sys.executable, str(SCRIPT_PATH), *args]
    completed = run(cmd, cwd=cwd, check=False)
    payload: Dict[str, object] = {}
    try:
        payload = parse_json_report(completed.stdout)
    except Exception:
        payload = {"parse_error": True}
    return completed.returncode, completed.stdout, completed.stderr, payload


def save_case_artifacts(case_id: str, stdout: str, stderr: str, payload: Dict[str, object]) -> Tuple[str, str, str]:
    case_dir = RUN_OUTPUT_ROOT / case_id
    stdout_path = case_dir / "stdout.txt"
    stderr_path = case_dir / "stderr.txt"
    payload_path = case_dir / "payload.json"
    write_text(stdout_path, stdout)
    write_text(stderr_path, stderr)
    write_json(payload_path, payload)
    return (
        str(payload_path.relative_to(REPO_ROOT)),
        str(stdout_path.relative_to(REPO_ROOT)),
        str(stderr_path.relative_to(REPO_ROOT)),
    )


def tc_001_integrate_dry_run() -> CaseResult:
    case_id = "TC-001"
    name = "integrate dry-run returns plan"
    case_dir = ENV_ROOT / case_id
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)

    workspace, _, _ = init_repo(case_dir)

    git(workspace, "checkout", "-b", "source-sync", "rebuild")
    (workspace / "feature.txt").write_text("feature\n", encoding="utf-8")
    git(workspace, "add", "feature.txt")
    git(workspace, "commit", "-m", "source change")
    git(workspace, "checkout", "main")
    git(workspace, "worktree", "add", str(case_dir / "wt-source"), "source-sync")

    rc, stdout, stderr, payload = run_skill(
        workspace,
        ["integrate", "--source", "source-sync", "--parent", "rebuild", "--remote", "origin"],
    )

    reasons: List[str] = []
    passed = True
    if rc != 0:
        passed = False
        reasons.append(f"return_code:{rc}!=0")
    if payload.get("mode") != "integrate":
        passed = False
        reasons.append("mode_not_integrate")
    if payload.get("dry_run") is not True:
        passed = False
        reasons.append("dry_run_not_true")
    if payload.get("result") != "ok":
        passed = False
        reasons.append("result_not_ok")

    payload_ref, stdout_ref, stderr_ref = save_case_artifacts(case_id, stdout, stderr, payload)
    return CaseResult(
        case_id=case_id,
        name=name,
        passed=passed,
        gate_decision="pass" if passed else "fail",
        reasons=reasons,
        return_code=rc,
        expected_return_code=0,
        payload_ref=payload_ref,
        stdout_ref=stdout_ref,
        stderr_ref=stderr_ref,
    )


def tc_002_fanout_skip_dirty() -> CaseResult:
    case_id = "TC-002"
    name = "fanout skips dirty sibling above threshold"
    case_dir = ENV_ROOT / case_id
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)

    workspace, _, _ = init_repo(case_dir)

    git(workspace, "checkout", "-b", "sibling-skip", "rebuild")
    git(workspace, "push", "-u", "origin", "sibling-skip")
    git(workspace, "checkout", "main")
    wt_sibling = case_dir / "wt-sibling-skip"
    git(workspace, "worktree", "add", str(wt_sibling), "sibling-skip")

    (wt_sibling / "dirty.txt").write_text("\n".join(["x" * 20 for _ in range(100)]) + "\n", encoding="utf-8")

    rc, stdout, stderr, payload = run_skill(
        workspace,
        [
            "fanout",
            "--parent",
            "rebuild",
            "--siblings",
            "sibling-skip",
            "--max-dirty-files",
            "1",
            "--max-dirty-lines",
            "10",
            "--remote",
            "origin",
            "--apply",
        ],
    )

    reasons: List[str] = []
    passed = True
    results = payload.get("results", [])
    first_status = None
    if isinstance(results, list) and results:
        first_status = results[0].get("status")

    if rc != 0:
        passed = False
        reasons.append(f"return_code:{rc}!=0")
    if first_status != "skipped":
        passed = False
        reasons.append(f"status_not_skipped:{first_status}")

    payload_ref, stdout_ref, stderr_ref = save_case_artifacts(case_id, stdout, stderr, payload)
    return CaseResult(
        case_id=case_id,
        name=name,
        passed=passed,
        gate_decision="pass" if passed else "fail",
        reasons=reasons,
        return_code=rc,
        expected_return_code=0,
        payload_ref=payload_ref,
        stdout_ref=stdout_ref,
        stderr_ref=stderr_ref,
    )


def tc_003_fanout_conflict_abort() -> CaseResult:
    case_id = "TC-003"
    name = "fanout conflict triggers manual_conflict and merge abort"
    case_dir = ENV_ROOT / case_id
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)

    workspace, wt_rebuild, _ = init_repo(case_dir)

    git(workspace, "checkout", "-b", "sibling-conflict", "rebuild")
    git(workspace, "push", "-u", "origin", "sibling-conflict")
    git(workspace, "checkout", "main")
    wt_sibling = case_dir / "wt-sibling-conflict"
    git(workspace, "worktree", "add", str(wt_sibling), "sibling-conflict")

    (wt_sibling / "conflict.txt").write_text("value-from-sibling\n", encoding="utf-8")
    git(wt_sibling, "add", "conflict.txt")
    git(wt_sibling, "commit", "-m", "sibling change")

    (wt_rebuild / "conflict.txt").write_text("value-from-parent\n", encoding="utf-8")
    git(wt_rebuild, "add", "conflict.txt")
    git(wt_rebuild, "commit", "-m", "parent change")

    rc, stdout, stderr, payload = run_skill(
        workspace,
        [
            "fanout",
            "--parent",
            "rebuild",
            "--siblings",
            "sibling-conflict",
            "--remote",
            "origin",
            "--apply",
        ],
    )

    reasons: List[str] = []
    passed = True
    status = None
    results = payload.get("results", [])
    if isinstance(results, list) and results:
        status = results[0].get("status")

    merge_head = git(wt_sibling, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False)

    if rc != 4:
        passed = False
        reasons.append(f"return_code:{rc}!=4")
    if status != "manual_conflict":
        passed = False
        reasons.append(f"status_not_manual_conflict:{status}")
    if merge_head.returncode == 0:
        passed = False
        reasons.append("merge_head_still_exists")

    payload_ref, stdout_ref, stderr_ref = save_case_artifacts(case_id, stdout, stderr, payload)
    return CaseResult(
        case_id=case_id,
        name=name,
        passed=passed,
        gate_decision="pass" if passed else "fail",
        reasons=reasons,
        return_code=rc,
        expected_return_code=4,
        payload_ref=payload_ref,
        stdout_ref=stdout_ref,
        stderr_ref=stderr_ref,
    )


def tc_004_upstream_remote_freshness() -> CaseResult:
    case_id = "TC-004"
    name = "fanout includes latest commit from non-default upstream remote"
    case_dir = ENV_ROOT / case_id
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)

    workspace, wt_rebuild, mirror_bare = init_repo(case_dir, with_mirror=True)

    git(workspace, "checkout", "-b", "sibling-mirror", "rebuild")
    (workspace / "sibling.txt").write_text("sibling-base\n", encoding="utf-8")
    git(workspace, "add", "sibling.txt")
    git(workspace, "commit", "-m", "sibling base")
    git(workspace, "push", "-u", "mirror", "sibling-mirror")
    git(workspace, "checkout", "main")
    wt_sibling = case_dir / "wt-sibling-mirror"
    git(workspace, "worktree", "add", str(wt_sibling), "sibling-mirror")

    writer = case_dir / "mirror-writer"
    git(case_dir, "clone", str(mirror_bare), str(writer))
    git(writer, "config", "user.name", "QA Bot")
    git(writer, "config", "user.email", "qa-bot@example.com")
    git(writer, "checkout", "sibling-mirror")
    (writer / "remote-only.txt").write_text("remote-latest\n", encoding="utf-8")
    git(writer, "add", "remote-only.txt")
    git(writer, "commit", "-m", "advance mirror branch")
    git(writer, "push", "origin", "sibling-mirror")

    latest_remote_commit = git(writer, "rev-parse", "HEAD").stdout.strip()

    (wt_rebuild / "parent-new.txt").write_text("parent-new\n", encoding="utf-8")
    git(wt_rebuild, "add", "parent-new.txt")
    git(wt_rebuild, "commit", "-m", "parent update")

    rc, stdout, stderr, payload = run_skill(
        workspace,
        [
            "fanout",
            "--parent",
            "rebuild",
            "--siblings",
            "sibling-mirror",
            "--remote",
            "origin",
            "--apply",
        ],
    )

    contains_remote = (
        git(workspace, "merge-base", "--is-ancestor", latest_remote_commit, "sibling-mirror", check=False).returncode
        == 0
    )

    payload["latest_remote_commit"] = latest_remote_commit
    payload["contains_latest_remote_commit"] = contains_remote

    reasons: List[str] = []
    passed = True
    status = None
    results = payload.get("results", [])
    if isinstance(results, list) and results:
        status = results[0].get("status")

    if rc != 0:
        passed = False
        reasons.append(f"return_code:{rc}!=0")
    if status != "ok":
        passed = False
        reasons.append(f"status_not_ok:{status}")
    if not contains_remote:
        passed = False
        reasons.append("missing_latest_upstream_commit")

    payload_ref, stdout_ref, stderr_ref = save_case_artifacts(case_id, stdout, stderr, payload)
    return CaseResult(
        case_id=case_id,
        name=name,
        passed=passed,
        gate_decision="pass" if passed else "fail",
        reasons=reasons,
        return_code=rc,
        expected_return_code=0,
        payload_ref=payload_ref,
        stdout_ref=stdout_ref,
        stderr_ref=stderr_ref,
    )


def render_report(results: List[CaseResult], gate_decision: str, reasons: List[str], summary_ref: str) -> str:
    lines = [
        "# git-worktree-sync Runtime Validation Report",
        "",
        f"- gate_decision: {gate_decision}",
        f"- summary_ref: {summary_ref}",
        "",
        "## Case Results",
    ]
    for result in results:
        lines.extend(
            [
                f"### {result.case_id} {result.name}",
                f"- decision: {result.gate_decision}",
                f"- return_code: {result.return_code} (expected {result.expected_return_code})",
                f"- payload_ref: {result.payload_ref}",
                f"- stdout_ref: {result.stdout_ref}",
                f"- stderr_ref: {result.stderr_ref}",
                f"- reasons: {', '.join(result.reasons) if result.reasons else '(none)'}",
                "",
            ]
        )

    lines.append("## Gate Reasons")
    if reasons:
        for reason in reasons:
            lines.append(f"- {reason}")
    else:
        lines.append("- all P0 cases passed")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    RUN_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    ENV_ROOT.mkdir(parents=True, exist_ok=True)

    results = [
        tc_001_integrate_dry_run(),
        tc_002_fanout_skip_dirty(),
        tc_003_fanout_conflict_abort(),
        tc_004_upstream_remote_freshness(),
    ]

    failed = [result for result in results if not result.passed]
    gate_decision = "pass" if not failed else "fail"
    reasons = [f"{result.case_id}: {','.join(result.reasons)}" for result in failed]

    summary_payload = {
        "gate_decision": gate_decision,
        "evidence_ref": str(RUN_OUTPUT_ROOT.relative_to(REPO_ROOT)),
        "reasons": reasons,
        "cases": [result.__dict__ for result in results],
    }

    summary_path = EVIDENCE_ROOT / "run_summary.json"
    report_path = EVIDENCE_ROOT / "report.md"
    write_json(summary_path, summary_payload)
    write_text(
        report_path,
        render_report(
            results=results,
            gate_decision=gate_decision,
            reasons=reasons,
            summary_ref=str(summary_path.relative_to(REPO_ROOT)),
        ),
    )

    print(json.dumps(summary_payload, indent=2, ensure_ascii=True))
    return 0 if gate_decision == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
