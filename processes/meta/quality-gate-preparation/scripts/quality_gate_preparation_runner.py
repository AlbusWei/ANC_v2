#!/usr/bin/env python3
"""Executable runner for quality-gate-preparation process."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class QualityGatePreparationError(RuntimeError):
    """Fail-closed runtime error for quality-gate-preparation."""


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
        raise QualityGatePreparationError("not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise QualityGatePreparationError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise QualityGatePreparationError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise QualityGatePreparationError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_cmd(cmd: List[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(root), check=False, capture_output=True, text=True)


def parse_last_json(stdout: str) -> Dict[str, Any]:
    for line in reversed([item.strip() for item in stdout.splitlines() if item.strip()]):
        if line.startswith("{") and line.endswith("}"):
            payload = json.loads(line)
            if isinstance(payload, dict):
                return payload
    raise QualityGatePreparationError("runner stdout does not contain json object")


def parse_risk_focus(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip().upper() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        items = [item.strip().strip("'\"") for item in text[1:-1].split(",")]
        return [item.upper() for item in items if item]
    return [item.strip().upper() for item in text.split(",") if item.strip()]


def count_test_cases(test_doc_path: Path) -> int:
    text = test_doc_path.read_text(encoding="utf-8")
    return sum(1 for line in text.splitlines() if line.strip().startswith("### TC-"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run quality-gate-preparation process")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--evidence-dir",
        default="",
        help="Evidence directory path (repo-relative). Default runtime_data/execution/evidence/bpm-runtime/w3b_qa_process_cases/<run_id>/quality-gate-preparation",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Optional run id for evidence directory naming",
    )
    parser.add_argument(
        "--profile-set",
        default="quality-gate.baseline@1.0.0",
        help="Comma-separated profile ids for AP-018/AP-019",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    request = load_json(input_path)

    run_id = args.run_id.strip() or datetime.now(timezone.utc).strftime("qa-prep-%Y%m%dT%H%M%SZ")
    evidence_dir = resolve_path(
        root,
        args.evidence_dir.strip()
        or f"runtime_data/execution/evidence/bpm-runtime/w3b_qa_process_cases/{run_id}/quality-gate-preparation",
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    runtime_trace_path = evidence_dir / "runtime_trace.json"
    fail_closed_path = evidence_dir / "fail_closed_record.json"

    phase_trace: List[Dict[str, Any]] = []

    try:
        required = ["objective_ref", "spec_ref", "test_doc_ref", "risk_focus", "superpower_ref"]
        missing = [key for key in required if key not in request]
        if missing:
            raise QualityGatePreparationError(f"missing required input fields: {','.join(missing)}")

        test_doc_path = resolve_path(root, str(request["test_doc_ref"]))
        if not test_doc_path.exists():
            raise QualityGatePreparationError("test_doc_ref_unreachable")

        superpower_ref = str(request["superpower_ref"])
        superpower_path = resolve_path(root, superpower_ref)
        if not superpower_path.exists():
            raise QualityGatePreparationError("superpower_ref_unreachable")

        risk_focus = parse_risk_focus(request.get("risk_focus"))
        if "P0" not in set(risk_focus):
            raise QualityGatePreparationError("risk_focus_missing_p0")

        case_count = count_test_cases(test_doc_path)
        if case_count == 0:
            raise QualityGatePreparationError("test_doc_has_no_cases")

        # p1: design-tests (AP-005) - keep deterministic and traceable from TEST.md source.
        p1_test_plan = evidence_dir / "p1_test_plan.json"
        test_plan_payload = {
            "timestamp": now_iso(),
            "objective_ref": request["objective_ref"],
            "spec_ref": request["spec_ref"],
            "test_doc_ref": to_rel(test_doc_path, root),
            "risk_focus": risk_focus,
            "case_count": case_count,
            "gate_decision": "pass",
            "coverage": {
                "p0_covered": True,
                "p0_rule": "risk_focus must include P0",
            },
        }
        dump_json(p1_test_plan, test_plan_payload)
        phase_trace.append(
            {
                "phase": "p1-design-tests",
                "status": "pass",
                "test_plan_ref": to_rel(p1_test_plan, root),
                "ts": now_iso(),
            }
        )

        # p2: compile-test-datapoints (AP-018)
        p2_dir = evidence_dir / "p2_test_compiler"
        p2_dir.mkdir(parents=True, exist_ok=True)
        compile_cmd = [
            sys.executable,
            "skills/system/qa/test-compiler/scripts/compile_test_doc.py",
            "--test-doc",
            to_rel(test_doc_path, root),
            "--objective-ref",
            str(request["objective_ref"]),
            "--spec-ref",
            str(request["spec_ref"]),
            "--profile-set",
            args.profile_set,
            "--output-dir",
            to_rel(p2_dir, root),
        ]
        compile_proc = run_cmd(compile_cmd, root)
        (p2_dir / "stdout.txt").write_text(compile_proc.stdout, encoding="utf-8")
        (p2_dir / "stderr.txt").write_text(compile_proc.stderr, encoding="utf-8")

        compile_payload = parse_last_json(compile_proc.stdout)
        compile_report_ref = compile_payload.get("compile_report_ref")
        if compile_proc.returncode != 0 or compile_payload.get("gate_decision") != "pass":
            raise QualityGatePreparationError(
                f"test_compiler_failed:rc={compile_proc.returncode}:gate={compile_payload.get('gate_decision')}"
            )
        if not isinstance(compile_report_ref, str) or not resolve_path(root, compile_report_ref).exists():
            raise QualityGatePreparationError("compile_report_missing")

        phase_trace.append(
            {
                "phase": "p2-compile-test-datapoints",
                "status": "pass",
                "return_code": compile_proc.returncode,
                "compile_report_ref": compile_report_ref,
                "ts": now_iso(),
            }
        )

        # p3: bind-test-profiles (AP-019)
        test_datapoints_ref = str(compile_payload.get("test_datapoints_ref") or "")
        tc_profile_map_ref = str(compile_payload.get("tc_profile_map_ref") or "")
        if not test_datapoints_ref or not resolve_path(root, test_datapoints_ref).exists():
            raise QualityGatePreparationError("test_datapoints_ref_missing")
        if not tc_profile_map_ref or not resolve_path(root, tc_profile_map_ref).exists():
            raise QualityGatePreparationError("tc_profile_map_ref_missing")

        bundle_path = evidence_dir / "preparation_bundle.index.json"
        bundle_payload = {
            "superpower_ref": to_rel(superpower_path, root),
            "objective_ref": request["objective_ref"],
            "spec_ref": request["spec_ref"],
            "test_doc_ref": to_rel(test_doc_path, root),
            "test_datapoints_ref": test_datapoints_ref,
            "tc_profile_map_ref": tc_profile_map_ref,
            "compile_report_ref": compile_report_ref,
            "producer_process_id": "quality-gate-preparation",
            "timestamps": {
                "generated_at": now_iso(),
            },
        }
        dump_json(bundle_path, bundle_payload)

        phase_trace.append(
            {
                "phase": "p3-bind-test-profiles",
                "status": "pass",
                "preparation_bundle_ref": to_rel(bundle_path, root),
                "ts": now_iso(),
            }
        )

        runtime_trace = {
            "timestamp": now_iso(),
            "process_id": "quality-gate-preparation",
            "status": "ok",
            "phase_trace": phase_trace,
            "input_ref": to_rel(input_path, root),
        }
        dump_json(runtime_trace_path, runtime_trace)

        output = {
            "status": "ok",
            "process_id": "quality-gate-preparation",
            "verdict": "pass",
            "test_plan_ref": to_rel(p1_test_plan, root),
            "test_datapoints_ref": test_datapoints_ref,
            "tc_profile_map_ref": tc_profile_map_ref,
            "compile_report_ref": compile_report_ref,
            "preparation_bundle_ref": to_rel(bundle_path, root),
            "preparation_evidence_ref": to_rel(evidence_dir, root),
            "runtime_trace_ref": to_rel(runtime_trace_path, root),
            "reasons": ["preparation_bundle_ready"],
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 0

    except Exception as exc:
        failure_reason = str(exc)
        dump_json(
            fail_closed_path,
            {
                "timestamp": now_iso(),
                "status": "failed",
                "reason": failure_reason,
                "fail_closed": True,
            },
        )
        dump_json(
            runtime_trace_path,
            {
                "timestamp": now_iso(),
                "process_id": "quality-gate-preparation",
                "status": "failed",
                "phase_trace": phase_trace,
                "reason": failure_reason,
                "fail_closed_record_ref": to_rel(fail_closed_path, root),
            },
        )
        output = {
            "status": "failed",
            "process_id": "quality-gate-preparation",
            "verdict": "test_invalid",
            "preparation_bundle_ref": "",
            "preparation_evidence_ref": to_rel(evidence_dir, root),
            "runtime_trace_ref": to_rel(runtime_trace_path, root),
            "fail_closed_record_ref": to_rel(fail_closed_path, root),
            "reasons": [failure_reason],
        }
        dump_json(output_path, output)
        print(to_rel(output_path, root))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
