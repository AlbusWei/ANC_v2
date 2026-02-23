#!/usr/bin/env python3
"""执行 TC-ONLINE-001~004，验证 M2 线上运行时可达性。"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


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
    fallback = None
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TC-ONLINE-001~004")
    parser.add_argument(
        "--report",
        default="docs/design/modules/evidence/bpm-runtime/w5_tc_online_report.json",
        help="Repo-relative report output path",
    )
    parser.add_argument(
        "--openclaw-profile",
        default="",
        help="Optional OpenClaw profile name",
    )
    return parser.parse_args()


def build_openclaw_cmd(profile: str, *args: str) -> List[str]:
    cmd = ["openclaw"]
    if profile:
        cmd.extend(["--profile", profile])
    cmd.extend(args)
    return cmd


def main() -> int:
    args = parse_args()
    root = repo_root()
    profile = args.openclaw_profile.strip()

    cases: List[Dict[str, Any]] = []

    # TC-ONLINE-001：网关健康检查
    cmd_health = build_openclaw_cmd(profile, "health", "--json")
    proc_health = run_cmd(cmd_health, root)
    payload_health = parse_json_from_mixed_output(proc_health.stdout)
    health_ok = proc_health.returncode == 0 and isinstance(payload_health, dict)
    append_case(
        cases,
        "TC-ONLINE-001",
        health_ok,
        {
            "return_code": proc_health.returncode,
            "stdout_tail": "\n".join(proc_health.stdout.splitlines()[-10:]),
            "stderr_tail": "\n".join(proc_health.stderr.splitlines()[-10:]),
        },
    )

    # TC-ONLINE-002：repoRoot 与当前 worktree 对齐
    cmd_repo_root = build_openclaw_cmd(profile, "config", "get", "agents.defaults.repoRoot", "--json")
    proc_repo_root = run_cmd(cmd_repo_root, root)
    payload_repo_root = parse_json_from_mixed_output(proc_repo_root.stdout)
    repo_root_ok = proc_repo_root.returncode == 0 and str(payload_repo_root).strip().strip('"') == str(root)
    append_case(
        cases,
        "TC-ONLINE-002",
        repo_root_ok,
        {
            "return_code": proc_repo_root.returncode,
            "repo_root_expected": str(root),
            "repo_root_actual": str(payload_repo_root).strip().strip('"'),
            "stderr_tail": "\n".join(proc_repo_root.stderr.splitlines()[-10:]),
        },
    )

    # TC-ONLINE-003：核心 agent 在运行时配置中可见
    cmd_agents = build_openclaw_cmd(profile, "config", "get", "agents.list", "--json")
    proc_agents = run_cmd(cmd_agents, root)
    payload_agents = parse_json_from_mixed_output(proc_agents.stdout)
    agent_ids: List[str] = []
    if isinstance(payload_agents, list):
        for item in payload_agents:
            if isinstance(item, dict):
                agent_id = item.get("id")
                if isinstance(agent_id, str):
                    agent_ids.append(agent_id)
    required_agents = {"bpm", "admin", "system-analyst"}
    agents_ok = proc_agents.returncode == 0 and required_agents.issubset(set(agent_ids))
    append_case(
        cases,
        "TC-ONLINE-003",
        agents_ok,
        {
            "return_code": proc_agents.returncode,
            "required_agents": sorted(required_agents),
            "loaded_agents": sorted(agent_ids),
            "stderr_tail": "\n".join(proc_agents.stderr.splitlines()[-10:]),
        },
    )

    # TC-ONLINE-004：核心 skill 与流程 skill 可加载
    required_skills = [
        "config-change-gatekeeper",
        "system-config-updater",
        "trigger-ingress-normalizer",
        "trigger-matcher-dedupe",
        "process-instance-manager",
        "system-feedback-digest",
        "trigger-schedule-runtime",
        "trigger-event-runtime",
        "runtime-policy-calibration",
    ]
    missing_skills: List[str] = []
    skill_details: Dict[str, Any] = {}
    for skill_name in required_skills:
        cmd_skill = build_openclaw_cmd(profile, "skills", "info", skill_name, "--json")
        proc_skill = run_cmd(cmd_skill, root)
        payload_skill = parse_json_from_mixed_output(proc_skill.stdout)
        ok = (
            proc_skill.returncode == 0
            and isinstance(payload_skill, dict)
            and payload_skill.get("eligible") is True
            and isinstance(payload_skill.get("filePath"), str)
        )
        if not ok:
            missing_skills.append(skill_name)
        skill_details[skill_name] = {
            "return_code": proc_skill.returncode,
            "eligible": payload_skill.get("eligible") if isinstance(payload_skill, dict) else None,
            "file_path": payload_skill.get("filePath") if isinstance(payload_skill, dict) else None,
        }
    append_case(
        cases,
        "TC-ONLINE-004",
        len(missing_skills) == 0,
        {
            "missing_skills": missing_skills,
            "skill_details": skill_details,
        },
    )

    passed = sum(1 for case in cases if case["status"] == "pass")
    failed = len(cases) - passed
    report = {
        "ts": now_iso(),
        "suite": "TC-ONLINE-001~004",
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "profile": profile or "default",
        "cases": cases,
    }

    report_path = (root / args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
