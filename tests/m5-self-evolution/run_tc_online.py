#!/usr/bin/env python3
"""执行 M5 线上运行用例：Batch 8~9 的 Hook/Cron/Heartbeat 真机回归。"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


HOOK_PACK_PATH = "tools/openclaw/hooks/anc-lifecycle-events"
HOOK_NAME = "lifecycle-event-bridge"
HOOK_DISPATCH_DIR = "runtime_data/evolution/hooks/dispatch"
HOOK_LOG_PATH = "runtime_data/evolution/hooks/logs/lifecycle-event-bridge.jsonl"
CRON_JOB_IMPROVEMENT = "m5-improvement-review"
CRON_JOB_OWNER_REMINDER = "m5-owner-review-reminder"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("not inside git repository")
    return Path(proc.stdout.strip()).resolve()


def run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


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


def append_case(cases: List[Dict[str, Any]], case_id: str, ok: bool, details: Dict[str, Any]) -> None:
    cases.append({"id": case_id, "status": "pass" if ok else "fail", "details": details})


def build_openclaw_cmd(profile: str, *args: str) -> List[str]:
    cmd = ["openclaw"]
    if profile:
        cmd.extend(["--profile", profile])
    cmd.extend(args)
    return cmd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run M5 online cases")
    parser.add_argument(
        "--report",
        default="runtime_data/execution/evidence/m5-self-evolution/w2_tc_online_report.json",
        help="Repo-relative report output path",
    )
    parser.add_argument(
        "--openclaw-profile",
        default="",
        help="Optional OpenClaw profile name",
    )
    return parser.parse_args()


def find_job_by_name(jobs_payload: Dict[str, Any], name: str) -> Dict[str, Any] | None:
    jobs = jobs_payload.get("jobs")
    if not isinstance(jobs, list):
        return None
    for item in jobs:
        if isinstance(item, dict) and str(item.get("name") or "") == name:
            return item
    return None


def ensure_cron_jobs(root: Path, profile: str) -> Dict[str, Any]:
    cmd_list = build_openclaw_cmd(profile, "cron", "list", "--json")

    proc_list_before = run_cmd(cmd_list, root)
    payload_before = parse_json_from_mixed_output(proc_list_before.stdout)
    # Gateway restart 后短窗口内可能返回空 job 列表，这里做短轮询避免重复创建。
    for _ in range(6):
        jobs = payload_before.get("jobs") if isinstance(payload_before, dict) else None
        if isinstance(jobs, list) and jobs:
            break
        time.sleep(1.0)
        proc_list_before = run_cmd(cmd_list, root)
        payload_before = parse_json_from_mixed_output(proc_list_before.stdout)

    if not isinstance(payload_before, dict):
        payload_before = {}

    created: List[str] = []
    details: Dict[str, Any] = {
        "created": created,
        "improvement_id": "",
        "owner_reminder_id": "",
    }

    improvement = find_job_by_name(payload_before, CRON_JOB_IMPROVEMENT)
    has_improvement_name = CRON_JOB_IMPROVEMENT in proc_list_before.stdout
    if improvement is None and not has_improvement_name:
        cmd_add_improvement = build_openclaw_cmd(
            profile,
            "cron",
            "add",
            "--name",
            CRON_JOB_IMPROVEMENT,
            "--cron",
            "20 */6 * * *",
            "--tz",
            "Asia/Shanghai",
            "--session",
            "isolated",
            "--message",
            "执行 improvement-review 周期评审：检查 runtime_data/evolution/hooks 最近 bridge 日志状态，并输出一段不超过80字的改进建议摘要。",
            "--no-deliver",
            "--json",
        )
        proc_add = run_cmd(cmd_add_improvement, root)
        payload_add = parse_json_from_mixed_output(proc_add.stdout)
        if proc_add.returncode != 0:
            raise RuntimeError(f"create cron job failed: {CRON_JOB_IMPROVEMENT}: {proc_add.stderr}")
        if isinstance(payload_add, dict):
            details["improvement_id"] = str(payload_add.get("id") or "")
        created.append(CRON_JOB_IMPROVEMENT)

    owner = find_job_by_name(payload_before, CRON_JOB_OWNER_REMINDER)
    has_owner_name = CRON_JOB_OWNER_REMINDER in proc_list_before.stdout
    if owner is None and not has_owner_name:
        cmd_add_owner = build_openclaw_cmd(
            profile,
            "cron",
            "add",
            "--name",
            CRON_JOB_OWNER_REMINDER,
            "--cron",
            "0 10 * * *",
            "--tz",
            "Asia/Shanghai",
            "--session",
            "main",
            "--system-event",
            "Owner评审提醒：下一次心跳请检查 M5 提案链路与风险项。",
            "--wake",
            "now",
            "--json",
        )
        proc_add_owner = run_cmd(cmd_add_owner, root)
        payload_add_owner = parse_json_from_mixed_output(proc_add_owner.stdout)
        if proc_add_owner.returncode != 0:
            raise RuntimeError(f"create cron job failed: {CRON_JOB_OWNER_REMINDER}: {proc_add_owner.stderr}")
        if isinstance(payload_add_owner, dict):
            details["owner_reminder_id"] = str(payload_add_owner.get("id") or "")
        created.append(CRON_JOB_OWNER_REMINDER)

    proc_list_after = run_cmd(cmd_list, root)
    payload_after = parse_json_from_mixed_output(proc_list_after.stdout)
    if not isinstance(payload_after, dict):
        payload_after = {}

    improvement_after = find_job_by_name(payload_after, CRON_JOB_IMPROVEMENT)
    owner_after = find_job_by_name(payload_after, CRON_JOB_OWNER_REMINDER)
    details["jobs_payload"] = payload_after

    if improvement_after:
        details["improvement_id"] = str(improvement_after.get("id") or details["improvement_id"])
    if owner_after:
        details["owner_reminder_id"] = str(owner_after.get("id") or details["owner_reminder_id"])

    details["improvement_tz"] = (
        ((improvement_after or {}).get("schedule") or {}).get("tz") if isinstance(improvement_after, dict) else None
    )
    details["owner_tz"] = (
        ((owner_after or {}).get("schedule") or {}).get("tz") if isinstance(owner_after, dict) else None
    )
    details["improvement_session"] = (improvement_after or {}).get("sessionTarget") if isinstance(improvement_after, dict) else None
    details["owner_session"] = (owner_after or {}).get("sessionTarget") if isinstance(owner_after, dict) else None
    return details


def main() -> int:
    args = parse_args()
    root = repo_root()
    profile = args.openclaw_profile.strip()

    cases: List[Dict[str, Any]] = []

    # TC-M5-HOOK-ONLINE-001: health
    cmd_health = build_openclaw_cmd(profile, "health", "--json")
    proc_health = run_cmd(cmd_health, root)
    payload_health = parse_json_from_mixed_output(proc_health.stdout)
    health_ok = proc_health.returncode == 0 and isinstance(payload_health, dict) and bool(payload_health.get("ok"))
    append_case(
        cases,
        "TC-M5-HOOK-ONLINE-001",
        health_ok,
        {
            "return_code": proc_health.returncode,
            "stdout_tail": "\n".join(proc_health.stdout.splitlines()[-8:]),
            "stderr_tail": "\n".join(proc_health.stderr.splitlines()[-8:]),
        },
    )

    # TC-M5-HOOK-ONLINE-002: hooks list/check
    cmd_hooks_list = build_openclaw_cmd(profile, "hooks", "list", "--json")
    proc_hooks_list = run_cmd(cmd_hooks_list, root)
    payload_hooks_list = parse_json_from_mixed_output(proc_hooks_list.stdout)
    hooks_entries = payload_hooks_list.get("hooks") if isinstance(payload_hooks_list, dict) else None
    hooks_list_ok = proc_hooks_list.returncode == 0 and isinstance(hooks_entries, list)

    cmd_hooks_check = build_openclaw_cmd(profile, "hooks", "check", "--json")
    proc_hooks_check = run_cmd(cmd_hooks_check, root)
    payload_hooks_check = parse_json_from_mixed_output(proc_hooks_check.stdout)
    hooks_check_ok = (
        proc_hooks_check.returncode == 0
        and isinstance(payload_hooks_check, dict)
        and isinstance(payload_hooks_check.get("hooks"), dict)
    )

    append_case(
        cases,
        "TC-M5-HOOK-ONLINE-002",
        hooks_list_ok and hooks_check_ok,
        {
            "hooks_list_return_code": proc_hooks_list.returncode,
            "hooks_check_return_code": proc_hooks_check.returncode,
            "hooks_count": len(hooks_entries) if isinstance(hooks_entries, list) else None,
            "hooks_check_total": payload_hooks_check.get("total") if isinstance(payload_hooks_check, dict) else None,
            "hooks_check_stderr_tail": "\n".join(proc_hooks_check.stderr.splitlines()[-8:]),
        },
    )

    # TC-M5-HOOK-ONLINE-003: cron status
    cmd_cron_status = build_openclaw_cmd(profile, "cron", "status", "--json")
    proc_cron_status = run_cmd(cmd_cron_status, root)
    payload_cron_status = parse_json_from_mixed_output(proc_cron_status.stdout)
    cron_ok = (
        proc_cron_status.returncode == 0
        and isinstance(payload_cron_status, dict)
        and payload_cron_status.get("enabled") is True
    )
    append_case(
        cases,
        "TC-M5-HOOK-ONLINE-003",
        cron_ok,
        {
            "return_code": proc_cron_status.returncode,
            "enabled": payload_cron_status.get("enabled") if isinstance(payload_cron_status, dict) else None,
            "stdout_tail": "\n".join(proc_cron_status.stdout.splitlines()[-8:]),
            "stderr_tail": "\n".join(proc_cron_status.stderr.splitlines()[-8:]),
        },
    )

    # TC-M5-HOOK-ONLINE-004: hook pack install + discovery
    cmd_link = build_openclaw_cmd(profile, "hooks", "install", "--link", HOOK_PACK_PATH)
    proc_link = run_cmd(cmd_link, root)
    link_ok = proc_link.returncode == 0 or "already exists" in (proc_link.stdout + proc_link.stderr)

    cmd_install = build_openclaw_cmd(profile, "hooks", "install", HOOK_PACK_PATH)
    proc_install = run_cmd(cmd_install, root)
    install_ok = proc_install.returncode == 0 or "already exists" in (proc_install.stdout + proc_install.stderr)

    proc_restart = run_cmd(build_openclaw_cmd(profile, "gateway", "restart"), root)
    proc_list_after_install = run_cmd(build_openclaw_cmd(profile, "hooks", "list", "--json"), root)
    payload_list_after_install = parse_json_from_mixed_output(proc_list_after_install.stdout)
    hooks_after_install = payload_list_after_install.get("hooks") if isinstance(payload_list_after_install, dict) else []
    hook_info = None
    if isinstance(hooks_after_install, list):
        for item in hooks_after_install:
            if isinstance(item, dict) and str(item.get("name") or "") == HOOK_NAME:
                hook_info = item
                break
    hook_discovered = isinstance(hook_info, dict) and bool(hook_info.get("eligible"))
    append_case(
        cases,
        "TC-M5-HOOK-ONLINE-004",
        link_ok and install_ok and proc_restart.returncode == 0 and hook_discovered,
        {
            "link_return_code": proc_link.returncode,
            "link_ok": link_ok,
            "install_return_code": proc_install.returncode,
            "restart_return_code": proc_restart.returncode,
            "hook_discovered": hook_discovered,
            "hook_source": hook_info.get("source") if isinstance(hook_info, dict) else None,
            "install_stdout_tail": "\n".join(proc_install.stdout.splitlines()[-6:]),
            "install_stderr_tail": "\n".join(proc_install.stderr.splitlines()[-6:]),
        },
    )

    # TC-M5-HOOK-ONLINE-005: restart triggers bridge and runtime output
    dispatch_dir = (root / HOOK_DISPATCH_DIR).resolve()
    dispatch_dir.mkdir(parents=True, exist_ok=True)
    before = time.time()
    before_count = len(list(dispatch_dir.glob("*.json")))
    proc_restart_for_bridge = run_cmd(build_openclaw_cmd(profile, "gateway", "restart"), root)

    newest_dispatch: Path | None = None
    deadline = time.time() + 30
    while time.time() < deadline:
        files = sorted(dispatch_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
        if files and files[0].stat().st_mtime >= before:
            newest_dispatch = files[0]
            break
        time.sleep(0.8)

    runtime_output_exists = False
    runtime_output_status = ""
    runtime_output_wait_seconds = 0.0
    after_count = len(list(dispatch_dir.glob("*.json")))
    newest_dispatch_rel = ""
    if newest_dispatch is not None:
        newest_dispatch_rel = newest_dispatch.resolve().relative_to(root).as_posix()
        payload_dispatch = parse_json_from_mixed_output(newest_dispatch.read_text(encoding="utf-8"))
        runtime_output_ref = str((payload_dispatch or {}).get("runtime_output_ref") or "")
        if runtime_output_ref:
            runtime_output_path = (root / runtime_output_ref).resolve()
            output_wait_start = time.time()
            output_deadline = output_wait_start + 60
            while time.time() < output_deadline:
                if runtime_output_path.exists():
                    runtime_output_exists = True
                    break
                time.sleep(0.8)
            runtime_output_wait_seconds = round(time.time() - output_wait_start, 2)
            if runtime_output_exists:
                runtime_output_payload = parse_json_from_mixed_output(runtime_output_path.read_text(encoding="utf-8"))
                runtime_output_status = str((runtime_output_payload or {}).get("status") or "")

    log_exists = (root / HOOK_LOG_PATH).exists()
    append_case(
        cases,
        "TC-M5-HOOK-ONLINE-005",
        proc_restart_for_bridge.returncode == 0
        and newest_dispatch is not None
        and after_count > before_count
        and runtime_output_exists
        and runtime_output_status in {"ok", "failed"}
        and log_exists,
        {
            "restart_return_code": proc_restart_for_bridge.returncode,
            "dispatch_before": before_count,
            "dispatch_after": after_count,
            "newest_dispatch_ref": newest_dispatch_rel,
            "runtime_output_exists": runtime_output_exists,
            "runtime_output_status": runtime_output_status,
            "runtime_output_wait_seconds": runtime_output_wait_seconds,
            "hook_log_exists": log_exists,
        },
    )

    # TC-M5-HOOK-ONLINE-006: cron jobs upsert + tz/session check
    cron_ok = True
    cron_details: Dict[str, Any] = {}
    try:
        cron_details = ensure_cron_jobs(root, profile)
        improvement_ok = (
            bool(cron_details.get("improvement_id"))
            and cron_details.get("improvement_tz") == "Asia/Shanghai"
            and cron_details.get("improvement_session") == "isolated"
        )
        owner_ok = (
            bool(cron_details.get("owner_reminder_id"))
            and cron_details.get("owner_tz") == "Asia/Shanghai"
            and cron_details.get("owner_session") == "main"
        )
        cron_ok = improvement_ok and owner_ok
    except Exception as exc:  # pragma: no cover - CLI/runtime 异常分支
        cron_ok = False
        cron_details = {"error": str(exc)}

    append_case(cases, "TC-M5-HOOK-ONLINE-006", cron_ok, cron_details)

    # TC-M5-HOOK-ONLINE-007: cron run + heartbeat last
    run_ok = False
    run_details: Dict[str, Any] = {}
    improvement_id = str(cron_details.get("improvement_id") or "")
    owner_id = str(cron_details.get("owner_reminder_id") or "")
    if improvement_id and owner_id:
        proc_run_improvement = run_cmd(
            build_openclaw_cmd(profile, "cron", "run", improvement_id, "--expect-final", "--timeout", "180000"),
            root,
        )
        proc_run_owner = run_cmd(
            build_openclaw_cmd(profile, "cron", "run", owner_id, "--expect-final", "--timeout", "180000"),
            root,
        )
        proc_runs_improvement = run_cmd(
            build_openclaw_cmd(profile, "cron", "runs", "--id", improvement_id, "--limit", "1"),
            root,
        )
        proc_runs_owner = run_cmd(
            build_openclaw_cmd(profile, "cron", "runs", "--id", owner_id, "--limit", "1"),
            root,
        )
        payload_runs_improvement = parse_json_from_mixed_output(proc_runs_improvement.stdout)
        payload_runs_owner = parse_json_from_mixed_output(proc_runs_owner.stdout)

        proc_hb_enable = run_cmd(build_openclaw_cmd(profile, "system", "heartbeat", "enable"), root)
        proc_system_event = run_cmd(
            build_openclaw_cmd(profile, "system", "event", "--mode", "now", "--text", "TC-M5 Batch9 heartbeat check", "--json"),
            root,
        )
        proc_hb_last = run_cmd(build_openclaw_cmd(profile, "system", "heartbeat", "last"), root)
        payload_hb_last = parse_json_from_mixed_output(proc_hb_last.stdout)

        entries_improvement = payload_runs_improvement.get("entries") if isinstance(payload_runs_improvement, dict) else None
        entries_owner = payload_runs_owner.get("entries") if isinstance(payload_runs_owner, dict) else None
        latest_improvement_ok = isinstance(entries_improvement, list) and bool(entries_improvement) and entries_improvement[0].get("status") == "ok"
        latest_owner_ok = isinstance(entries_owner, list) and bool(entries_owner) and entries_owner[0].get("status") == "ok"
        heartbeat_ok = isinstance(payload_hb_last, dict) and bool(payload_hb_last.get("status"))

        run_ok = (
            proc_run_improvement.returncode == 0
            and proc_run_owner.returncode == 0
            and latest_improvement_ok
            and latest_owner_ok
            and proc_hb_enable.returncode == 0
            and proc_system_event.returncode == 0
            and heartbeat_ok
        )
        run_details = {
            "run_improvement_return_code": proc_run_improvement.returncode,
            "run_owner_return_code": proc_run_owner.returncode,
            "latest_improvement_ok": latest_improvement_ok,
            "latest_owner_ok": latest_owner_ok,
            "heartbeat_last": payload_hb_last,
        }
    else:
        run_details = {
            "error": "cron job ids unavailable",
            "improvement_id": improvement_id,
            "owner_id": owner_id,
        }

    append_case(cases, "TC-M5-HOOK-ONLINE-007", run_ok, run_details)

    passed = sum(1 for case in cases if case["status"] == "pass")
    failed = len(cases) - passed
    report = {
        "ts": now_iso(),
        "suite": "TC-M5-HOOK-ONLINE-001~007",
        "profile": profile or "default",
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "cases": cases,
    }

    report_path = (root / args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
