#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

EXIT_SUCCESS = 0
EXIT_UNEXPECTED_ERROR = 1
EXIT_FAIL_CLOSED = 2

REQUIRED_FIELDS = ["template_ref", "schema_ref", "target_asset_ref", "validation_profile"]
VALIDATION_PROFILES = {"strict", "standard", "lenient"}


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
        "validation_report_ref": (report_path.as_posix() if report_path else output_path.as_posix()),
        "gate_decision": "fail",
        "blocking_issues": [{"reason_code": reason_code, "message": message, "details": details}],
        "exit_code": EXIT_FAIL_CLOSED,
    }
    write_json(output_path, payload)
    if report_path is not None:
        write_json(report_path, {"runner": "template_validator_runner", "decision": "fail_closed", "reason_code": reason_code, "details": details})
    return EXIT_FAIL_CLOSED


def main() -> int:
    parser = argparse.ArgumentParser(description="Template validator runner")
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
                message="关键输入字段缺失。",
                details={"missing_fields": missing_fields},
            )

        profile = str(data["validation_profile"]).strip().lower()
        if profile not in VALIDATION_PROFILES:
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="invalid_validation_profile",
                message="validation_profile 非法。",
                details={"validation_profile": profile, "allowed": sorted(VALIDATION_PROFILES)},
            )

        refs = {
            "template_ref": Path(str(data["template_ref"])),
            "schema_ref": Path(str(data["schema_ref"])),
            "target_asset_ref": Path(str(data["target_asset_ref"])),
        }
        missing_refs: List[Dict[str, str]] = []
        for field, ref_path in refs.items():
            if not ref_path.exists() or not ref_path.is_file():
                missing_refs.append({"field": field, "path": ref_path.as_posix()})

        if missing_refs:
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="missing_references",
                message="存在不可读取的模板或 schema 引用。",
                details={"missing_refs": missing_refs},
            )

        blocking_issues: List[Dict[str, Any]] = []
        expected_keys = data.get("expected_keys", [])
        if expected_keys:
            try:
                target_payload = read_json(refs["target_asset_ref"])
            except Exception as exc:  # noqa: BLE001
                return fail_closed(
                    output_path=output_path,
                    report_path=report_path,
                    reason_code="target_asset_unreadable",
                    message="target_asset_ref 无法解析为 JSON。",
                    details={"error": str(exc)},
                )

            missing_expected = [key for key in expected_keys if key not in target_payload]
            if missing_expected:
                blocking_issues.append(
                    {
                        "reason_code": "schema_mismatch",
                        "message": "target 资产缺失 expected_keys",
                        "details": {"missing_expected": missing_expected},
                    }
                )

        if blocking_issues:
            payload = {
                "status": "fail_closed",
                "validation_report_ref": (report_path.as_posix() if report_path else output_path.as_posix()),
                "gate_decision": "fail",
                "blocking_issues": blocking_issues,
                "exit_code": EXIT_FAIL_CLOSED,
            }
            write_json(output_path, payload)
            if report_path is not None:
                write_json(report_path, {"runner": "template_validator_runner", "decision": "fail_closed", "blocking_issues": blocking_issues})
            return EXIT_FAIL_CLOSED

        payload = {
            "status": "success",
            "validation_report_ref": (report_path.as_posix() if report_path else output_path.as_posix()),
            "gate_decision": "pass",
            "blocking_issues": [],
            "checked_refs": {key: path.as_posix() for key, path in refs.items()},
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "exit_code": EXIT_SUCCESS,
        }
        write_json(output_path, payload)

        if report_path is not None:
            write_json(
                report_path,
                {
                    "runner": "template_validator_runner",
                    "decision": "success",
                    "profile": profile,
                    "checked_refs": payload["checked_refs"],
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
            write_json(report_path, {"runner": "template_validator_runner", "decision": "error", "error": str(exc)})
        print(f"unexpected error: {exc}", file=sys.stderr)
        return EXIT_UNEXPECTED_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
