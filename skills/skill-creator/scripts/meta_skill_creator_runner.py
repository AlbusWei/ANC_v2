#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from scaffold_skill import scaffold_skill

EXIT_SUCCESS = 0
EXIT_UNEXPECTED_ERROR = 1
EXIT_FAIL_CLOSED = 2

REQUIRED_FIELDS = ["skill_name", "layer", "namespace", "objective_ref"]


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
        write_json(report_path, {"runner": "meta_skill_creator_runner", "decision": "fail_closed", "reason_code": reason_code, "details": details})
    return EXIT_FAIL_CLOSED


def main() -> int:
    parser = argparse.ArgumentParser(description="meta-skill-creator runner")
    parser.add_argument("--input", required=True, help="输入 JSON 路径")
    parser.add_argument("--output", required=True, help="输出 JSON 路径")
    parser.add_argument("--report", help="可选报告 JSON 路径")
    parser.add_argument("--force", action="store_true", help="覆盖已存在文件")
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
                message="关键输入字段缺失。",
                details={"missing_fields": missing_fields},
            )

        try:
            scaffold_result = scaffold_skill(
                skill_name=str(data["skill_name"]),
                layer=str(data["layer"]),
                namespace=str(data["namespace"]),
                objective_ref=str(data["objective_ref"]),
                description=str(data.get("description") or "由 meta-skill-creator 生成的技能骨架"),
                output_root=str(data.get("output_root") or "skills"),
                force=args.force,
            )
        except ValueError as exc:
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="invalid_input_contract",
                message=str(exc),
                details={"input": data},
            )

        payload = {
            "status": "success",
            "skill_id": "meta.arch.skill-creator",
            "name": "meta-skill-creator",
            "skill_md_path": scaffold_result["skill_md"],
            "test_doc_path": scaffold_result["test_doc"],
            "registry_patch_plan": {
                "skill_id": "meta.arch.skill-creator",
                "name": "meta-skill-creator",
                "status": "review",
                "version": "0.2.0",
                "tests": {
                    "test_doc": scaffold_result["test_doc"],
                    "methodology_ref": "docs/architecture/test_methodology.md",
                },
            },
            "review_evidence_ref": "docs/design/modules/evidence/self-development/e2e-online/session4-foundation/latest/",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "exit_code": EXIT_SUCCESS,
        }
        write_json(output_path, payload)

        if report_path is not None:
            write_json(
                report_path,
                {
                    "runner": "meta_skill_creator_runner",
                    "decision": "success",
                    "scaffold_result": scaffold_result,
                    "alias_policy": {
                        "runtime_name": "meta-skill-creator",
                        "historical_alias": "skill-creator",
                        "alias_usage": "documentation_only",
                    },
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
            write_json(report_path, {"runner": "meta_skill_creator_runner", "decision": "error", "error": str(exc)})
        print(f"unexpected error: {exc}", file=sys.stderr)
        return EXIT_UNEXPECTED_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
