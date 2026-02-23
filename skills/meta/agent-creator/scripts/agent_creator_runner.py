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

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_FIELDS = ["agent_id", "role_scope", "interfaces", "owner"]


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
        write_json(
            report_path,
            {
                "runner": "agent_creator_runner",
                "decision": "fail_closed",
                "reason_code": reason_code,
                "details": details,
            },
        )
    return EXIT_FAIL_CLOSED


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent creator runner")
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

        agent_id = str(data["agent_id"]).strip()
        owner = str(data["owner"]).strip()
        role_scope = data["role_scope"]
        interfaces = data["interfaces"]

        if not NAME_PATTERN.fullmatch(agent_id):
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="invalid_agent_id",
                message="agent_id 不符合 kebab-case 约束。",
                details={"agent_id": agent_id},
            )

        if not NAME_PATTERN.fullmatch(owner):
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="invalid_owner",
                message="owner 不符合命名约束。",
                details={"owner": owner},
            )

        if not isinstance(role_scope, dict) or not role_scope.get("responsibilities") or not role_scope.get("boundaries"):
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="invalid_role_scope",
                message="role_scope 必须同时包含 responsibilities 与 boundaries。",
                details={"role_scope": role_scope},
            )

        if not isinstance(interfaces, list) or not interfaces:
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="invalid_interfaces",
                message="interfaces 必须为非空数组。",
                details={"interfaces": interfaces},
            )

        invalid_interfaces: List[Dict[str, Any]] = []
        for index, interface in enumerate(interfaces):
            if not isinstance(interface, dict) or not str(interface.get("protocol_ref", "")).strip():
                invalid_interfaces.append({"index": index, "interface": interface})

        if invalid_interfaces:
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="invalid_protocol_refs",
                message="interfaces 中存在缺失 protocol_ref 的条目。",
                details={"invalid_interfaces": invalid_interfaces},
            )

        payload = {
            "status": "success",
            "skill_id": "meta.arch.agent-creator",
            "agent_doc_path": f"docs/design/agents/{agent_id}.md",
            "tools_doc_path": f"agents/{agent_id}/TOOLS.md",
            "registry_patch_plan": {
                "skill_id": "meta.arch.agent-creator",
                "name": "agent-creator",
                "status": "review",
                "tests": {
                    "test_doc": "skills/meta/agent-creator/TEST.md",
                    "methodology_ref": "docs/architecture/test_methodology.md",
                },
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "exit_code": EXIT_SUCCESS,
        }
        write_json(output_path, payload)

        if report_path is not None:
            write_json(
                report_path,
                {
                    "runner": "agent_creator_runner",
                    "decision": "success",
                    "checked_fields": REQUIRED_FIELDS,
                    "output_fields": ["agent_doc_path", "tools_doc_path", "registry_patch_plan"],
                },
            )
        return EXIT_SUCCESS

    except Exception as exc:  # noqa: BLE001
        error_payload = {
            "status": "error",
            "reason_code": "unexpected_error",
            "message": str(exc),
            "exit_code": EXIT_UNEXPECTED_ERROR,
        }
        write_json(output_path, error_payload)
        if report_path is not None:
            write_json(report_path, {"runner": "agent_creator_runner", "decision": "error", "error": str(exc)})
        print(f"unexpected error: {exc}", file=sys.stderr)
        return EXIT_UNEXPECTED_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
