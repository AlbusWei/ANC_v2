#!/usr/bin/env python3
"""objective-scope-baseline 可执行 runner。

职责：
1. 消费 objective_context_ref。
2. 调用 meta.arch.objective-writer runner 生成 objective。
3. 产出 scope_baseline_ref，供后续 spec/test 流程复用。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class ObjectiveScopeBaselineError(RuntimeError):
    """objective-scope-baseline 的 Fail-Closed 异常。"""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / ".git").exists():
            return parent
    raise ObjectiveScopeBaselineError("not inside git repository")


def resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else (root / path).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ObjectiveScopeBaselineError(f"missing_file:{path}") from exc
    except json.JSONDecodeError as exc:
        raise ObjectiveScopeBaselineError(f"invalid_json:{path}:{exc}") from exc
    if not isinstance(payload, dict):
        raise ObjectiveScopeBaselineError("json_root_must_be_object")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run objective-scope-baseline")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--evidence-dir", default="", help="Evidence dir path")
    parser.add_argument("--run-id", default="", help="Optional run id")
    parser.add_argument(
        "--objective-writer-runner",
        default="skills/meta/objective-writer/scripts/objective_writer_runner.py",
        help="Repo-relative objective-writer runner path",
    )
    return parser.parse_args()


def write_fail_closed(root: Path, output_path: Path, evidence_dir: Path, reason: str) -> int:
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
            "process_id": "objective-scope-baseline",
            "status": "failed",
            "reason": reason,
            "fail_closed_record_ref": to_rel(fail_record, root),
        },
    )
    dump_json(
        output_path,
        {
            "status": "failed",
            "process_id": "objective-scope-baseline",
            "reason_code": reason,
            "objective_ref": "",
            "scope_baseline_ref": "",
            "runtime_trace_ref": to_rel(runtime_trace, root),
            "fail_closed_record_ref": to_rel(fail_record, root),
        },
    )
    print(json.dumps({"status": "fail_closed", "output_ref": to_rel(output_path, root)}, ensure_ascii=False))
    return 2


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    run_id = args.run_id.strip() or datetime.now(timezone.utc).strftime("objective-scope-%Y%m%dT%H%M%SZ")
    evidence_dir = resolve_path(root, args.evidence_dir) if args.evidence_dir.strip() else (output_path.parent / run_id)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    try:
        request = load_json(input_path)
        objective_context_ref = str(request.get("objective_context_ref") or "").strip()
        if not objective_context_ref:
            raise ObjectiveScopeBaselineError("missing_required_field:objective_context_ref")

        objective_context_path = resolve_path(root, objective_context_ref)
        if not objective_context_path.exists():
            raise ObjectiveScopeBaselineError("objective_context_ref_unreachable")

        objective_context = objective_context_path.read_text(encoding="utf-8").strip()
        if not objective_context:
            raise ObjectiveScopeBaselineError("objective_context_empty")

        writer_runner = resolve_path(root, args.objective_writer_runner)
        if not writer_runner.exists():
            raise ObjectiveScopeBaselineError(f"objective_writer_runner_not_found:{writer_runner}")

        writer_input = evidence_dir / "objective_writer_input.json"
        writer_output = evidence_dir / "objective_writer_output.json"
        writer_evidence = evidence_dir / "objective_writer"

        dump_json(
            writer_input,
            {
                "objective_context": objective_context,
                "stakeholders": [
                    {"role": "owner", "name": "architect"},
                    {"role": "reviewer", "name": "bpm"},
                ],
                "constraints": {
                    "in_scope": ["目标澄清", "范围边界收敛"],
                    "non_goals": ["直接修改实现代码", "绕过质量门禁"],
                },
                "success_criteria": [
                    "至少 1 条 objective_ref 输出，并可追溯到输入上下文。",
                    "范围基线必须包含 2 类字段：in_scope 与 out_of_scope。",
                ],
            },
        )

        cmd = [
            sys.executable,
            to_rel(writer_runner, root),
            "--input",
            to_rel(writer_input, root),
            "--output",
            to_rel(writer_output, root),
            "--evidence-dir",
            to_rel(writer_evidence, root),
        ]
        proc = run_cmd(cmd, root)
        (evidence_dir / "objective_writer.stdout.log").write_text(proc.stdout, encoding="utf-8")
        (evidence_dir / "objective_writer.stderr.log").write_text(proc.stderr, encoding="utf-8")

        if proc.returncode != 0:
            raise ObjectiveScopeBaselineError(f"objective_writer_failed:rc={proc.returncode}")
        if not writer_output.exists():
            raise ObjectiveScopeBaselineError("objective_writer_output_missing")

        writer_payload = load_json(writer_output)
        objective_ref = str(writer_payload.get("objective_ref") or "").strip()
        if not objective_ref:
            raise ObjectiveScopeBaselineError("objective_ref_missing")

        scope_baseline_path = evidence_dir / "scope_baseline.json"
        scope_baseline = {
            "objective_ref": objective_ref,
            "in_scope": writer_payload.get("scope_baseline", {}).get("in_scope", []),
            "out_of_scope": writer_payload.get("non_goals", []),
            "baseline_policy": {
                "owner": "architect",
                "reviewer": "bpm",
                "lifecycle_target": "review",
            },
            "generated_at": now_iso(),
        }
        dump_json(scope_baseline_path, scope_baseline)

        runtime_trace = evidence_dir / "runtime_trace.json"
        dump_json(
            runtime_trace,
            {
                "timestamp": now_iso(),
                "process_id": "objective-scope-baseline",
                "status": "ok",
                "input_ref": to_rel(input_path, root),
                "objective_writer_output_ref": to_rel(writer_output, root),
                "scope_baseline_ref": to_rel(scope_baseline_path, root),
            },
        )

        output_payload = {
            "status": "ok",
            "process_id": "objective-scope-baseline",
            "objective_ref": objective_ref,
            "scope_baseline_ref": to_rel(scope_baseline_path, root),
            "objective_writer_output_ref": to_rel(writer_output, root),
            "runtime_trace_ref": to_rel(runtime_trace, root),
        }
        dump_json(output_path, output_payload)
        print(json.dumps({"status": "ok", "output_ref": to_rel(output_path, root)}, ensure_ascii=False))
        return 0
    except ObjectiveScopeBaselineError as exc:
        return write_fail_closed(root, output_path, evidence_dir, str(exc))
    except Exception as exc:  # noqa: BLE001
        runtime_error = evidence_dir / "runtime_error.json"
        dump_json(runtime_error, {"timestamp": now_iso(), "error": str(exc)})
        dump_json(
            output_path,
            {
                "status": "error",
                "process_id": "objective-scope-baseline",
                "reason_code": "unexpected_error",
                "error": str(exc),
                "runtime_error_ref": to_rel(runtime_error, root),
            },
        )
        print(json.dumps({"status": "error", "output_ref": to_rel(output_path, root)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
