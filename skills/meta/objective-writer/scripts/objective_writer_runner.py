#!/usr/bin/env python3
"""meta.arch.objective-writer 最小可执行 runner。

设计约束：
1. 输入契约不满足时 Fail-Closed（返回码 2）。
2. 运行异常返回码 1。
3. 产物输出包含 objective/scope/non_goals，可直接被下游流程消费。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class ObjectiveWriterError(RuntimeError):
    """objective-writer 的 Fail-Closed 业务异常。"""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / ".git").exists():
            return parent
    raise ObjectiveWriterError("not inside git repository")


def resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else (root / path).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ObjectiveWriterError(f"missing_file:{path}") from exc
    except json.JSONDecodeError as exc:
        raise ObjectiveWriterError(f"invalid_json:{path}:{exc}") from exc
    if not isinstance(payload, dict):
        raise ObjectiveWriterError("json_root_must_be_object")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dump_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run meta.arch.objective-writer")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--report", default="", help="Optional report JSON path")
    parser.add_argument("--evidence-dir", default="", help="Optional evidence directory path")
    return parser.parse_args()


def ensure_non_empty_str(payload: Dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ObjectiveWriterError(f"missing_required_field:{field}")
    return value.strip()


def ensure_stakeholders(payload: Dict[str, Any]) -> List[str]:
    raw = payload.get("stakeholders")
    if not isinstance(raw, list) or not raw:
        raise ObjectiveWriterError("missing_required_field:stakeholders")

    names: List[str] = []
    has_owner = False
    for item in raw:
        if isinstance(item, str) and item.strip():
            text = item.strip()
            names.append(text)
            if "owner" in text.lower() or "负责人" in text:
                has_owner = True
            continue
        if isinstance(item, dict):
            role = str(item.get("role") or "").strip()
            name = str(item.get("name") or item.get("id") or role).strip()
            if name:
                names.append(name)
            if role.lower() == "owner" or role == "负责人":
                has_owner = True

    if not names:
        raise ObjectiveWriterError("stakeholders_empty")
    if not has_owner:
        raise ObjectiveWriterError("stakeholders_missing_owner")
    return names


def parse_constraints(payload: Dict[str, Any]) -> Dict[str, Any]:
    constraints = payload.get("constraints")
    if not isinstance(constraints, dict):
        raise ObjectiveWriterError("missing_required_field:constraints")

    non_goals = constraints.get("non_goals")
    if isinstance(non_goals, str):
        non_goals_list = [non_goals.strip()] if non_goals.strip() else []
    elif isinstance(non_goals, list):
        non_goals_list = [str(item).strip() for item in non_goals if str(item).strip()]
    else:
        non_goals_list = []

    if not non_goals_list:
        raise ObjectiveWriterError("constraints_missing_non_goals")

    in_scope = constraints.get("in_scope")
    if isinstance(in_scope, str):
        in_scope_list = [in_scope.strip()] if in_scope.strip() else []
    elif isinstance(in_scope, list):
        in_scope_list = [str(item).strip() for item in in_scope if str(item).strip()]
    else:
        in_scope_list = []

    return {
        "raw": constraints,
        "in_scope": in_scope_list,
        "non_goals": non_goals_list,
    }


def parse_success_criteria(payload: Dict[str, Any]) -> List[str]:
    raw = payload.get("success_criteria")
    if not isinstance(raw, list) or not raw:
        raise ObjectiveWriterError("missing_required_field:success_criteria")

    measurable_signals = re.compile(r"(\d|>=|<=|%|ms|秒|分钟|小时|天|次|条|通过|失败|pass|fail|不超过|至少)", re.IGNORECASE)
    parsed: List[str] = []
    unverifiable: List[str] = []
    for item in raw:
        text = str(item).strip()
        if not text:
            continue
        parsed.append(text)
        if len(text) < 6 or measurable_signals.search(text) is None:
            unverifiable.append(text)

    if not parsed:
        raise ObjectiveWriterError("success_criteria_empty")
    if unverifiable:
        raise ObjectiveWriterError("unverifiable_success_criteria:" + " | ".join(unverifiable))
    return parsed


def build_objective_ref(objective_context: str) -> str:
    digest = hashlib.sha1(objective_context.encode("utf-8")).hexdigest()[:10]
    return f"obj-auto-{digest}"


def write_fail_closed(
    *,
    root: Path,
    output_path: Path,
    evidence_dir: Path,
    reason: str,
    report_path: Path | None,
) -> int:
    fail_record = evidence_dir / "fail_closed_record.json"
    runtime_trace = evidence_dir / "runtime_trace.json"
    dump_json(
        fail_record,
        {
            "timestamp": now_iso(),
            "status": "failed",
            "reason": reason,
            "fail_closed": True,
        },
    )
    dump_json(
        runtime_trace,
        {
            "timestamp": now_iso(),
            "skill_id": "meta.arch.objective-writer",
            "status": "failed",
            "reason": reason,
            "fail_closed_record_ref": to_rel(fail_record, root),
        },
    )

    output_payload = {
        "status": "fail_closed",
        "reason_code": reason,
        "objective_ref": "",
        "objective_statement": "",
        "success_criteria": [],
        "scope_baseline": {},
        "non_goals": [],
        "runtime_trace_ref": to_rel(runtime_trace, root),
        "fail_closed_record_ref": to_rel(fail_record, root),
    }
    dump_json(output_path, output_payload)

    if report_path is not None:
        dump_json(
            report_path,
            {
                "status": "fail_closed",
                "reason_code": reason,
                "output_ref": to_rel(output_path, root),
                "runtime_trace_ref": to_rel(runtime_trace, root),
            },
        )

    print(json.dumps({"status": "fail_closed", "output_ref": to_rel(output_path, root)}, ensure_ascii=False))
    return 2


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    report_path = resolve_path(root, args.report) if args.report.strip() else None
    evidence_dir = resolve_path(root, args.evidence_dir) if args.evidence_dir.strip() else (output_path.parent / "objective_writer_evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    try:
        request = load_json(input_path)
        objective_context = ensure_non_empty_str(request, "objective_context")
        stakeholders = ensure_stakeholders(request)
        constraints = parse_constraints(request)
        success_criteria = parse_success_criteria(request)

        objective_ref = build_objective_ref(objective_context)
        objective_statement = objective_context.splitlines()[0][:160] if objective_context.splitlines() else objective_context[:160]

        objective_doc = evidence_dir / "objective_statement.md"
        dump_text(
            objective_doc,
            "\n".join(
                [
                    f"# Objective {objective_ref}",
                    "",
                    "## Objective Statement",
                    objective_statement,
                    "",
                    "## Success Criteria",
                    *[f"- {item}" for item in success_criteria],
                    "",
                    "## Scope Baseline",
                    *([f"- in_scope: {item}" for item in constraints["in_scope"]] or ["- in_scope: 待下游补充"]),
                    "",
                    "## Non Goals",
                    *[f"- {item}" for item in constraints["non_goals"]],
                    "",
                    "## Stakeholders",
                    *[f"- {item}" for item in stakeholders],
                ]
            ),
        )

        scope_baseline = {
            "in_scope": constraints["in_scope"],
            "out_of_scope": constraints["non_goals"],
            "constraints_ref": to_rel(input_path, root),
        }

        runtime_trace = evidence_dir / "runtime_trace.json"
        dump_json(
            runtime_trace,
            {
                "timestamp": now_iso(),
                "skill_id": "meta.arch.objective-writer",
                "status": "ok",
                "input_ref": to_rel(input_path, root),
                "objective_doc_ref": to_rel(objective_doc, root),
                "objective_ref": objective_ref,
            },
        )

        output_payload = {
            "status": "ok",
            "objective_ref": objective_ref,
            "objective_statement": objective_statement,
            "success_criteria": success_criteria,
            "scope_baseline": scope_baseline,
            "non_goals": constraints["non_goals"],
            "stakeholders": stakeholders,
            "objective_doc_ref": to_rel(objective_doc, root),
            "runtime_trace_ref": to_rel(runtime_trace, root),
            "generated_at": now_iso(),
        }
        dump_json(output_path, output_payload)

        if report_path is not None:
            dump_json(
                report_path,
                {
                    "status": "ok",
                    "output_ref": to_rel(output_path, root),
                    "objective_ref": objective_ref,
                },
            )

        print(json.dumps({"status": "ok", "output_ref": to_rel(output_path, root), "objective_ref": objective_ref}, ensure_ascii=False))
        return 0
    except ObjectiveWriterError as exc:
        return write_fail_closed(
            root=root,
            output_path=output_path,
            evidence_dir=evidence_dir,
            reason=str(exc),
            report_path=report_path,
        )
    except Exception as exc:  # noqa: BLE001
        runtime_error = evidence_dir / "runtime_error.json"
        dump_json(runtime_error, {"timestamp": now_iso(), "error": str(exc)})
        dump_json(
            output_path,
            {
                "status": "error",
                "reason_code": "unexpected_error",
                "error": str(exc),
                "runtime_error_ref": to_rel(runtime_error, root),
            },
        )
        print(json.dumps({"status": "error", "output_ref": to_rel(output_path, root)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
