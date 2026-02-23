#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

EXIT_SUCCESS = 0
EXIT_UNEXPECTED_ERROR = 1
EXIT_FAIL_CLOSED = 2

PROCESS_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_FIELDS = ["process_id", "process_level", "phases", "control_flow", "fail_policy"]
VALID_PROCESS_LEVELS = {"p0", "p1", "p2", "p3", "p4", "p5", "p6"}


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fail_closed(
    *,
    output_path: Path,
    report_path: Path | None,
    reason_code: str,
    message: str,
    details: Dict[str, Any],
) -> int:
    payload = {
        "status": "fail_closed",
        "reason_code": reason_code,
        "message": message,
        "details": details,
        "exit_code": EXIT_FAIL_CLOSED,
    }
    write_json(output_path, payload)
    if report_path is not None:
        write_json(report_path, {"runner": "process_creator_runner", "decision": "fail_closed", "reason_code": reason_code, "details": details})
    return EXIT_FAIL_CLOSED


def main() -> int:
    parser = argparse.ArgumentParser(description="Process creator runner")
    parser.add_argument("--input", required=True, help="输入 JSON 路径")
    parser.add_argument("--output", required=True, help="输出 JSON 路径")
    parser.add_argument("--report", help="可选报告 JSON 路径")
    args = parser.parse_args()

    output_path = Path(args.output)
    report_path = Path(args.report) if args.report else None

    try:
        data = read_json(Path(args.input))

        missing_fields = [field for field in REQUIRED_FIELDS if field not in data or data[field] in (None, "", [])]
        if missing_fields:
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="missing_required_fields",
                message="关键输入字段缺失，拒绝继续执行。",
                details={"missing_fields": missing_fields},
            )

        process_id = str(data["process_id"]).strip()
        process_level = str(data["process_level"]).strip().lower()
        phases = data["phases"]
        control_flow = data["control_flow"]
        fail_policy = data["fail_policy"]

        if not PROCESS_ID_PATTERN.fullmatch(process_id):
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="invalid_process_id",
                message="process_id 不符合 kebab-case 约束。",
                details={"process_id": process_id},
            )

        if process_level not in VALID_PROCESS_LEVELS:
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="invalid_process_level",
                message="process_level 非法。",
                details={"process_level": process_level, "allowed": sorted(VALID_PROCESS_LEVELS)},
            )

        if not isinstance(phases, list) or not phases:
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="invalid_phases",
                message="phases 必须是非空数组。",
                details={"phases": phases},
            )

        invalid_phases: List[Dict[str, Any]] = []
        continuity_breaks: List[Dict[str, Any]] = []
        for index, phase in enumerate(phases):
            if not isinstance(phase, dict):
                invalid_phases.append({"index": index, "reason": "phase_not_object", "phase": phase})
                continue

            for key in ("phase_id", "target_type", "target_id", "requires_spec"):
                if key not in phase:
                    invalid_phases.append({"index": index, "reason": f"missing_{key}", "phase": phase})

            if bool(phase.get("requires_spec")) and not str(phase.get("spec_ref", "")).strip():
                invalid_phases.append({"index": index, "reason": "missing_spec_ref", "phase": phase})

            if index > 0:
                prev_seq = phases[index - 1].get("sequence") if isinstance(phases[index - 1], dict) else None
                curr_seq = phase.get("sequence")
                if prev_seq is not None and curr_seq is not None and curr_seq != prev_seq + 1:
                    continuity_breaks.append({"index": index, "previous_sequence": prev_seq, "current_sequence": curr_seq})

        if invalid_phases:
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="phase_closure_violation",
                message="phase 字段不闭合或 spec 引用缺失。",
                details={"invalid_phases": invalid_phases},
            )

        if continuity_breaks:
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="continuity_violation",
                message="检测到 phase 序列不连续。",
                details={"continuity_breaks": continuity_breaks},
            )

        if not isinstance(control_flow, dict) or not control_flow.get("start") or not control_flow.get("terminal"):
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="invalid_control_flow",
                message="control_flow 必须同时定义 start 与 terminal。",
                details={"control_flow": control_flow},
            )

        if not isinstance(fail_policy, dict) or not fail_policy.get("on_fail"):
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="invalid_fail_policy",
                message="fail_policy 必须包含 on_fail 策略。",
                details={"fail_policy": fail_policy},
            )

        base_dir = Path("processes/meta") / process_id
        payload = {
            "status": "success",
            "skill_id": "meta.arch.process-creator",
            "process_manifest_path": (base_dir / "process.json").as_posix(),
            "process_skill_path": (base_dir / "SKILL.md").as_posix(),
            "process_guide_path": (base_dir / "PROCESS.md").as_posix(),
            "registry_patch_plan": {
                "process_id": process_id,
                "status": "review",
                "version": "0.1.0",
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "exit_code": EXIT_SUCCESS,
        }
        write_json(output_path, payload)

        if report_path is not None:
            write_json(
                report_path,
                {
                    "runner": "process_creator_runner",
                    "decision": "success",
                    "checked_fields": REQUIRED_FIELDS,
                    "phase_count": len(phases),
                },
            )

        return EXIT_SUCCESS

    except Exception as exc:  # noqa: BLE001
        write_json(
            output_path,
            {
                "status": "error",
                "reason_code": "unexpected_error",
                "message": str(exc),
                "exit_code": EXIT_UNEXPECTED_ERROR,
            },
        )
        if report_path is not None:
            write_json(report_path, {"runner": "process_creator_runner", "decision": "error", "error": str(exc)})
        print(f"unexpected error: {exc}", file=sys.stderr)
        return EXIT_UNEXPECTED_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
