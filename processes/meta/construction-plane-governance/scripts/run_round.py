#!/usr/bin/env python3
"""CLI runner for construction-plane-governance round execution."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


ROUND_ID_RE = re.compile(r"^R-\d{8}-M6-[a-z0-9-]+-\d{2}$")


class RoundRunError(RuntimeError):
    """Fail-closed runtime error."""


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
        raise RoundRunError("Not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def run_cmd(cmd: List[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(root), check=False, capture_output=True, text=True)


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RoundRunError(f"missing input file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RoundRunError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RoundRunError("input payload must be object")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def dump_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def ensure_required(payload: Dict[str, Any], keys: List[str]) -> None:
    for key in keys:
        if key not in payload:
            raise RoundRunError(f"missing required field: {key}")


def default_checkpoint_events(changed_assets: List[str]) -> List[Dict[str, Any]]:
    return [
        {
            "entire_checkpoint_id": "cpk-sim-01",
            "commit_sha": "simulated-commit-01",
            "changed_files": changed_assets,
            "sync_status": "in_sync",
        },
        {
            "entire_checkpoint_id": "cpk-sim-02",
            "commit_sha": "simulated-commit-02",
            "changed_files": changed_assets,
            "sync_status": "in_sync",
        },
    ]


def write_phase_log(round_dir: Path, phase: str, payload: Dict[str, Any]) -> None:
    dump_json(round_dir / f"{phase}.json", payload)


def call_manual_task(
    root: Path,
    manual_input_path: Path,
    manual_output_path: Path,
) -> Dict[str, Any]:
    proc = run_cmd(
        [
            "python3",
            "skills/system/manual-task/scripts/manual_task_runner.py",
            "--input",
            to_rel(manual_input_path, root),
            "--output",
            to_rel(manual_output_path, root),
        ],
        root,
    )
    if proc.returncode != 0:
        raise RoundRunError(
            f"manual_task_runner failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return load_json(manual_output_path)


def call_round_event_tool(root: Path, args: List[str]) -> None:
    proc = run_cmd(
        [
            "python3",
            "processes/meta/construction-plane-governance/scripts/round_evidence_tool.py",
            *args,
        ],
        root,
    )
    if proc.returncode != 0:
        raise RoundRunError(f"round_evidence_tool failed: {' '.join(args)}\n{proc.stdout}\n{proc.stderr}")


def call_construction_audit(
    root: Path,
    audit_input_path: Path,
    audit_output_path: Path,
    report_rel: str,
) -> Dict[str, Any]:
    proc = run_cmd(
        [
            "python3",
            "skills/system/construction-audit/scripts/construction_audit.py",
            "--input",
            to_rel(audit_input_path, root),
            "--output",
            to_rel(audit_output_path, root),
            "--report",
            report_rel,
        ],
        root,
    )
    if proc.returncode != 0:
        raise RoundRunError(
            f"construction_audit failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return load_json(audit_output_path)


def call_superpower_sync(
    root: Path,
    args: List[str],
) -> subprocess.CompletedProcess[str]:
    cmd = [
        "bash",
        "skills/system/superpower-sync/scripts/superpower_sync.sh",
        *args,
    ]
    return run_cmd(cmd, root)


def run_registry_verify(root: Path, log_rel: str) -> None:
    proc = run_cmd(["python3", "shared/registry/registry_contract_tool.py", "verify"], root)
    log_lines = [
        "# registry verify output",
        "",
        "## stdout",
        proc.stdout.strip(),
        "",
        "## stderr",
        proc.stderr.strip(),
        "",
        f"returncode={proc.returncode}",
    ]
    dump_text(root / log_rel, "\n".join(log_lines))
    if proc.returncode != 0:
        raise RoundRunError("registry verify failed during p5")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run construction-plane-governance round")
    parser.add_argument("--input", required=True, help="Round input JSON path")
    parser.add_argument(
        "--round-dir",
        default=None,
        help="Round evidence directory (repo-relative). Default runtime_data/execution/evidence/construction-plane/<round_id>",
    )
    parser.add_argument("--git-range", default=None, help="Optional git range for trailer checks")
    parser.add_argument(
        "--scenario",
        default="A",
        choices=["A", "B", "C", "custom"],
        help="Dry-run scenario hint",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = root / input_path

    payload = load_json(input_path)
    ensure_required(
        payload,
        [
            "round_id",
            "round_goal",
            "change_scope_ref",
            "changed_assets",
            "linkage_targets",
            "owner",
            "superpower_ref",
        ],
    )

    round_id = payload["round_id"]
    if not isinstance(round_id, str) or ROUND_ID_RE.match(round_id) is None:
        raise RoundRunError(f"round_id invalid: {round_id!r}")

    changed_assets = payload["changed_assets"]
    if not isinstance(changed_assets, list) or not changed_assets:
        raise RoundRunError("changed_assets must be non-empty list")

    round_dir_rel = args.round_dir or f"runtime_data/execution/evidence/construction-plane/{round_id}"
    round_dir = root / round_dir_rel
    round_dir.mkdir(parents=True, exist_ok=True)

    result_path = round_dir / "round-result.json"
    round_log_path = round_dir / "round-evidence.jsonl"
    superpower_record_rel = f"{round_dir_rel}/superpower-sync-record.json"

    result: Dict[str, Any] = {
        "round_id": round_id,
        "scenario": args.scenario,
        "status": "running",
        "started_at": now_iso(),
        "round_dir": round_dir_rel,
        "phases": [],
    }

    def fail(phase: str, reason: str) -> int:
        result["status"] = "failed"
        result["failed_phase"] = phase
        result["reason"] = reason
        result["finished_at"] = now_iso()
        dump_json(result_path, result)
        print(to_rel(result_path, root))
        return 1

    try:
        # p1
        p1_input = {
            "objective_ref": "obj-m6-construction-plane-governance",
            "task_ref": "docs/design/processes/atomic/AP-032-construction-round-intake-baseline.md",
            "acceptance_criteria": "scope baseline includes module boundary and linkage targets",
            "expected_outputs": {
                "scope_baseline_ref": f"{round_dir_rel}/scope_baseline.md",
            },
            "payload": {
                "scope_baseline_ref": (
                    "# Scope Baseline\n"
                    f"round_id: {payload['round_id']}\n"
                    f"round_goal: {payload['round_goal']}\n"
                    f"change_scope_ref: {payload['change_scope_ref']}\n"
                    f"changed_assets_count: {len(changed_assets)}\n"
                    f"linkage_targets: {json.dumps(payload['linkage_targets'], ensure_ascii=False)}\n"
                    f"superpower_ref: {payload['superpower_ref']}\n"
                ),
            },
            "reason": "scope baseline generated",
        }
        p1_input_path = round_dir / "p1-manual-input.json"
        p1_output_path = round_dir / "p1-manual-output.json"
        dump_json(p1_input_path, p1_input)
        p1_output = call_manual_task(root, p1_input_path, p1_output_path)
        scope_baseline_ref = p1_output["generated_refs"]["scope_baseline_ref"]
        result["phases"].append({"phase": "p1", "status": "completed", "scope_baseline_ref": scope_baseline_ref})

        call_round_event_tool(
            root,
            [
                "open",
                "--log",
                to_rel(round_log_path, root),
                "--round-id",
                payload["round_id"],
                "--superpower-ref",
                payload["superpower_ref"],
                "--round-goal",
                payload["round_goal"],
                "--owner",
                payload["owner"],
            ],
        )

        checkpoint_events = payload.get("checkpoint_events")
        if not isinstance(checkpoint_events, list) or not checkpoint_events:
            checkpoint_events = default_checkpoint_events(changed_assets)

        for idx, cp in enumerate(checkpoint_events, start=1):
            checkpoint_id = cp.get("entire_checkpoint_id", f"cpk-sim-{idx:02d}")
            commit_sha = cp.get("commit_sha", f"simulated-commit-{idx:02d}")
            sync_status = cp.get("sync_status", "in_sync")
            cp_files = cp.get("changed_files", changed_assets)
            cmd = [
                "checkpoint",
                "--log",
                to_rel(round_log_path, root),
                "--round-id",
                payload["round_id"],
                "--superpower-ref",
                payload["superpower_ref"],
                "--checkpoint-id",
                str(checkpoint_id),
                "--commit-sha",
                str(commit_sha),
                "--sync-status",
                str(sync_status),
            ]
            for changed in cp_files:
                cmd.extend(["--changed-file", str(changed)])
            call_round_event_tool(root, cmd)

        # p2
        p2_input = {
            "round_id": payload["round_id"],
            "scope_baseline_ref": scope_baseline_ref,
            "linkage_targets": payload["linkage_targets"],
            "changed_assets": changed_assets,
            "superpower_ref": payload["superpower_ref"],
        }
        p2_input_path = round_dir / "p2-audit-input.json"
        p2_output_path = round_dir / "p2-audit-output.json"
        dump_json(p2_input_path, p2_input)
        p2_output = call_construction_audit(
            root,
            p2_input_path,
            p2_output_path,
            report_rel=f"{round_dir_rel}/linkage_report.md",
        )
        result["phases"].append({"phase": "p2", "status": "completed", **p2_output})

        # p3
        open_questions = payload.get("open_questions")
        if not isinstance(open_questions, list):
            open_questions = []

        conflict_snapshot = args.scenario == "C"
        if conflict_snapshot:
            decision_snapshot_content = (
                "# Decision Snapshot\n"
                "decision: conflict-not-resolved\n"
                "conflict_state: unresolved\n"
                "owner: architect\n"
            )
        else:
            decision_snapshot_content = (
                "# Decision Snapshot\n"
                "decision: aligned\n"
                "conflict_state: resolved\n"
                "owner: architect\n"
            )

        p3_input = {
            "objective_ref": "obj-m6-construction-plane-governance",
            "task_ref": "docs/design/processes/atomic/AP-034-linked-artifacts-update.md",
            "acceptance_criteria": "all required linked artifacts are updated in the same round",
            "expected_outputs": {
                "m6_update_bundle_ref": f"{round_dir_rel}/m6_update_bundle.json",
                "construction_plane_delta_ref": f"{round_dir_rel}/construction_plane_delta.md",
                "open_questions_ref": f"{round_dir_rel}/open_questions.md",
                "decision_snapshot_ref": f"{round_dir_rel}/decision_snapshot.md",
            },
            "payload": {
                "m6_update_bundle_ref": {
                    "round_id": payload["round_id"],
                    "changed_assets": changed_assets,
                    "linkage_report_ref": p2_output["linkage_report_ref"],
                    "generated_at": now_iso(),
                },
                "construction_plane_delta_ref": (
                    "# Construction Plane Delta\n"
                    f"round_id: {payload['round_id']}\n"
                    f"changed_assets: {json.dumps(changed_assets, ensure_ascii=False)}\n"
                ),
                "open_questions_ref": (
                    "# Open Questions\n"
                    + ("\n".join(f"- {x}" for x in open_questions) if open_questions else "- (none)\n")
                ),
                "decision_snapshot_ref": decision_snapshot_content,
            },
            "reason": "linked artifacts generated",
        }
        p3_input_path = round_dir / "p3-manual-input.json"
        p3_output_path = round_dir / "p3-manual-output.json"
        dump_json(p3_input_path, p3_input)
        p3_output = call_manual_task(root, p3_input_path, p3_output_path)
        result["phases"].append(
            {
                "phase": "p3",
                "status": "completed",
                **p3_output["generated_refs"],
            }
        )

        checkpoint_count = len(checkpoint_events)
        commit_count_for_p4 = checkpoint_count

        anc_design_refs = payload.get("anc_design_refs")
        if not isinstance(anc_design_refs, list) or not anc_design_refs:
            anc_design_refs = [x for x in changed_assets if str(x).startswith("docs/design/")]
            if not anc_design_refs:
                anc_design_refs = changed_assets

        # p4
        sync_args: List[str] = [
            "--round-id",
            payload["round_id"],
            "--round-goal",
            payload["round_goal"],
            "--superpower-ref",
            payload["superpower_ref"],
            "--decision-snapshot-ref",
            p3_output["generated_refs"]["decision_snapshot_ref"],
            "--sync-actor",
            payload.get("sync_actor", "architect"),
            "--trigger-mode",
            payload.get("trigger_mode", "change_triggered"),
            "--risk-level",
            payload.get("risk_level", "medium"),
            "--checkpoint-count",
            str(checkpoint_count),
            "--commit-count",
            str(commit_count_for_p4),
            "--round-evidence-log-ref",
            to_rel(round_log_path, root),
            "--output-ref",
            superpower_record_rel,
        ]
        for item in anc_design_refs:
            sync_args.extend(["--anc-design-ref", str(item)])

        p4_proc: subprocess.CompletedProcess[str]
        if shutil.which("superpower") is None and args.scenario in {"A", "B"}:
            mock_sync_record = {
                "record_id": f"sps-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
                "round_id": payload["round_id"],
                "round_goal": payload["round_goal"],
                "module_scope": ["M6"],
                "owner": "architect",
                "superpower_ref": payload["superpower_ref"],
                "anc_design_refs": anc_design_refs,
                "decision_snapshot_ref": p3_output["generated_refs"]["decision_snapshot_ref"],
                "sync_status": "in_sync",
                "sync_timestamp": now_iso(),
                "sync_actor": payload.get("sync_actor", "architect"),
                "trigger_mode": payload.get("trigger_mode", "change_triggered"),
                "inspection_profile": {
                    "cadence_mode": "adaptive",
                    "cadence_hint": "risk-driven",
                    "primary_signal": "change_density",
                },
                "risk_level": payload.get("risk_level", "medium"),
                "conflict_state": {
                    "has_conflict": False,
                    "resolved": True,
                    "resolution_ref": p3_output["generated_refs"]["decision_snapshot_ref"],
                },
                "checkpoint_count": checkpoint_count,
                "commit_count": commit_count_for_p4,
                "evidence_bundle": {
                    "superpower_linkage_ref": "mock://superpower/show",
                    "anc_delta_index_ref": "",
                    "sync_check_report_ref": "mock://superpower/validate",
                    "status_report_ref": "mock://superpower/status",
                    "round_evidence_log_ref": to_rel(round_log_path, root),
                },
                "sync_actions": [
                    {"action": "superpower_show", "result": "ok"},
                    {"action": "superpower_status", "result": "ok"},
                    {"action": "superpower_validate_strict", "result": "ok"},
                ],
            }
            dump_json(root / superpower_record_rel, mock_sync_record)
            p4_proc = subprocess.CompletedProcess(
                args=["mock-superpower-sync"],
                returncode=0,
                stdout=f"{superpower_record_rel}\n",
                stderr="",
            )
        else:
            p4_proc = call_superpower_sync(root, sync_args)
        if p4_proc.returncode != 0:
            result["phases"].append(
                {
                    "phase": "p4",
                    "status": "failed",
                    "stdout": p4_proc.stdout,
                    "stderr": p4_proc.stderr,
                }
            )
            return fail("p4", "superpower sync blocked/conflict")

        superpower_record = load_json(root / superpower_record_rel)
        result["phases"].append(
            {
                "phase": "p4",
                "status": "completed",
                "superpower_sync_ref": superpower_record_rel,
                "sync_status": superpower_record.get("sync_status"),
            }
        )

        # p5
        registry_verify_ref = f"{round_dir_rel}/registry_verify.log"
        run_registry_verify(root, registry_verify_ref)

        close_commit_count = checkpoint_count
        if args.scenario == "B":
            close_commit_count = checkpoint_count + 1

        call_round_event_tool(
            root,
            [
                "close",
                "--log",
                to_rel(round_log_path, root),
                "--round-id",
                payload["round_id"],
                "--superpower-ref",
                payload["superpower_ref"],
                "--decision-snapshot-ref",
                p3_output["generated_refs"]["decision_snapshot_ref"],
                "--final-sync-status",
                str(superpower_record.get("sync_status", "in_sync")),
                "--checkpoint-count",
                str(checkpoint_count),
                "--commit-count",
                str(close_commit_count),
                "--verdict",
                "pass",
            ],
        )

        verify_cmd = [
            "python3",
            "processes/meta/construction-plane-governance/scripts/round_evidence_tool.py",
            "verify",
            "--log",
            to_rel(round_log_path, root),
            "--json",
        ]
        if args.git_range:
            verify_cmd.extend(["--git-range", args.git_range])
        p5_verify_proc = run_cmd(verify_cmd, root)
        verify_report_ref = f"{round_dir_rel}/round_evidence_verify.json"
        if p5_verify_proc.stdout.strip():
            (root / verify_report_ref).write_text(p5_verify_proc.stdout, encoding="utf-8")
        if p5_verify_proc.returncode != 0:
            result["phases"].append(
                {
                    "phase": "p5",
                    "status": "failed",
                    "verify_report_ref": verify_report_ref,
                }
            )
            return fail("p5", "round evidence verify failed")

        p5_input = {
            "objective_ref": "obj-m6-construction-plane-governance",
            "task_ref": "docs/design/processes/atomic/AP-036-construction-round-close-verification.md",
            "acceptance_criteria": "registry verification passed and open questions are owned",
            "expected_outputs": {
                "round_close_summary_ref": f"{round_dir_rel}/round_close_summary.md",
            },
            "payload": {
                "round_close_summary_ref": (
                    "# Round Close Summary\n"
                    f"round_id: {payload['round_id']}\n"
                    f"superpower_ref: {payload['superpower_ref']}\n"
                    f"checkpoint_count: {checkpoint_count}\n"
                    f"commit_count: {close_commit_count}\n"
                    f"superpower_sync_ref: {superpower_record_rel}\n"
                    f"registry_verify_report_ref: {registry_verify_ref}\n"
                    f"round_evidence_log_ref: {to_rel(round_log_path, root)}\n"
                    f"round_evidence_verify_ref: {verify_report_ref}\n"
                ),
            },
            "reason": "close verification summary generated",
        }
        p5_input_path = round_dir / "p5-manual-input.json"
        p5_output_path = round_dir / "p5-manual-output.json"
        dump_json(p5_input_path, p5_input)
        p5_output = call_manual_task(root, p5_input_path, p5_output_path)
        round_close_summary_ref = p5_output["generated_refs"]["round_close_summary_ref"]

        final_output = {
            "m6_update_bundle_ref": p3_output["generated_refs"]["m6_update_bundle_ref"],
            "linkage_report_ref": p2_output["linkage_report_ref"],
            "superpower_sync_ref": superpower_record_rel,
            "registry_verify_report_ref": registry_verify_ref,
            "construction_plane_delta_ref": p3_output["generated_refs"]["construction_plane_delta_ref"],
            "open_questions_ref": p3_output["generated_refs"]["open_questions_ref"],
            "round_evidence_log_ref": to_rel(round_log_path, root),
            "round_close_summary_ref": round_close_summary_ref,
        }
        dump_json(round_dir / "round-output.json", final_output)

        result["status"] = "passed"
        result["finished_at"] = now_iso()
        result["output_ref"] = to_rel(round_dir / "round-output.json", root)
        result["phases"].append({"phase": "p5", "status": "completed"})
        dump_json(result_path, result)
        print(to_rel(result_path, root))
        return 0

    except RoundRunError as exc:
        return fail("runtime", str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
