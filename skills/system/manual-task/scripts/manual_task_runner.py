#!/usr/bin/env python3
"""Execute BPM actor task with natural-language guidance and archive evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


REPO_REL_PATTERN = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$)).+")
DEFAULT_RULE_REF = "docs/architecture/process_architecture.md#61-phase-输入拼接与跨-phase-交接规则"


class ManualTaskError(RuntimeError):
    """Fail-closed error for manual task runner."""


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
        raise ManualTaskError("Not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManualTaskError(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManualTaskError(f"Input JSON invalid: {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ManualTaskError("Input payload must be a JSON object")
    return payload


def ensure_repo_rel_path(raw: str, field: str) -> str:
    if not isinstance(raw, str) or re.match(REPO_REL_PATTERN, raw) is None:
        raise ManualTaskError(f"{field} must be a repo-relative path without '..': {raw!r}")
    return raw


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def dump_text(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        content = payload
    else:
        content = json.dumps(payload, indent=2, ensure_ascii=False)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def dump_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, list):
        lines = [json.dumps(item, ensure_ascii=False) for item in payload]
        content = "\n".join(lines)
    else:
        content = json.dumps(payload, ensure_ascii=False)
    if content and not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def write_output_artifact(path: Path, payload: Any) -> None:
    if path.suffix == ".json":
        dump_json(path, payload)
    elif path.suffix == ".jsonl":
        dump_jsonl(path, payload)
    else:
        dump_text(path, payload)


def detect_dispatch_payload(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    dispatch = payload.get("task_dispatch")
    if isinstance(dispatch, dict):
        return dispatch
    dispatch = payload.get("dispatch")
    if isinstance(dispatch, dict):
        return dispatch
    return None


def validate_dispatch_payload(dispatch: Dict[str, Any]) -> None:
    required = [
        "instance_id",
        "phase_id",
        "actor",
        "lineage_ref",
        "stack_depth",
        "objective_ref",
        "session_binding",
        "evidence_dir",
    ]
    for key in required:
        if key not in dispatch:
            raise ManualTaskError(f"dispatch missing required field: {key}")

    binding = dispatch.get("session_binding")
    if not isinstance(binding, dict):
        raise ManualTaskError("dispatch.session_binding must be object")
    session_id = str(binding.get("session_id") or "").strip()
    if not session_id:
        raise ManualTaskError("dispatch.session_binding.session_id required")

    evidence_dir = str(dispatch.get("evidence_dir") or "").strip()
    ensure_repo_rel_path(evidence_dir, "dispatch.evidence_dir")


def validate_legacy_payload(payload: Dict[str, Any], root: Path) -> None:
    required = ["objective_ref", "task_ref", "acceptance_criteria", "expected_outputs"]
    for key in required:
        if key not in payload:
            raise ManualTaskError(f"missing required field: {key}")

    task_ref = str(payload["task_ref"])
    ensure_repo_rel_path(task_ref, "task_ref")
    if "#" not in task_ref and not (root / task_ref).exists():
        raise ManualTaskError(f"task_ref not reachable: {task_ref}")

    acceptance = payload["acceptance_criteria"]
    if not isinstance(acceptance, str) or not acceptance.strip():
        raise ManualTaskError("acceptance_criteria must be a non-empty string")


def validate_expected_outputs(expected_outputs: Dict[str, str]) -> None:
    if not isinstance(expected_outputs, dict) or not expected_outputs:
        raise ManualTaskError("expected_outputs must be a non-empty object")
    for key, path in expected_outputs.items():
        if not isinstance(key, str) or not key.strip():
            raise ManualTaskError("expected_outputs keys must be non-empty strings")
        ensure_repo_rel_path(path, f"expected_outputs.{key}")


def default_dispatch_outputs(dispatch: Dict[str, Any]) -> Dict[str, str]:
    evidence_dir = str(dispatch.get("evidence_dir") or "").strip().rstrip("/")
    phase_id = str(dispatch.get("phase_id") or "phase")
    return {
        "output_ref": f"{evidence_dir}/{phase_id}_manual_output.md",
        "completion_ref": f"{evidence_dir}/{phase_id}_task_completion.json",
    }


def normalize_payload(payload: Dict[str, Any], root: Path) -> Dict[str, Any]:
    dispatch = detect_dispatch_payload(payload)
    if dispatch is None:
        validate_legacy_payload(payload, root)
        expected_outputs = payload.get("expected_outputs")
        validate_expected_outputs(expected_outputs)
        return {
            "mode": "legacy",
            "dispatch": None,
            "objective_ref": str(payload["objective_ref"]),
            "task_ref": str(payload["task_ref"]),
            "acceptance_criteria": str(payload["acceptance_criteria"]),
            "expected_outputs": expected_outputs,
            "decision": str(payload.get("decision", "pass")),
            "reason": str(payload.get("reason", "manual task completed")),
            "payload_map": payload.get("payload", {}),
            "evidence_ref": payload.get("evidence_ref"),
        }

    validate_dispatch_payload(dispatch)
    objective_ref = str(payload.get("objective_ref") or dispatch.get("objective_ref") or "").strip()
    if not objective_ref:
        raise ManualTaskError("objective_ref is required")

    task_ref = str(payload.get("task_ref") or DEFAULT_RULE_REF)
    acceptance = str(
        payload.get("acceptance_criteria")
        or "按 BPM 分发上下文执行任务，并提供可追溯输出引用与 self_check。"
    ).strip()
    if not acceptance:
        raise ManualTaskError("acceptance_criteria must be non-empty")

    expected_outputs = payload.get("expected_outputs")
    if not isinstance(expected_outputs, dict) or not expected_outputs:
        expected_outputs = default_dispatch_outputs(dispatch)
    else:
        for key, value in default_dispatch_outputs(dispatch).items():
            expected_outputs.setdefault(key, value)
    validate_expected_outputs(expected_outputs)

    reason_default = f"phase {dispatch.get('phase_id')} task completed"
    return {
        "mode": "dispatch",
        "dispatch": dispatch,
        "objective_ref": objective_ref,
        "task_ref": task_ref,
        "acceptance_criteria": acceptance,
        "expected_outputs": expected_outputs,
        "decision": str(payload.get("decision", "pass")),
        "reason": str(payload.get("reason", reason_default)),
        "payload_map": payload.get("payload", {}),
        "evidence_ref": payload.get("evidence_ref"),
    }


def run_manual_task(payload: Dict[str, Any], root: Path) -> Dict[str, Any]:
    normalized = normalize_payload(payload, root)
    expected_outputs: Dict[str, str] = normalized["expected_outputs"]

    payload_map = normalized.get("payload_map", {})
    if payload_map is None:
        payload_map = {}
    if not isinstance(payload_map, dict):
        raise ManualTaskError("payload must be an object when provided")

    decision = str(normalized["decision"]).strip().lower()
    if decision not in {"pass", "fail"}:
        raise ManualTaskError("decision must be pass or fail")

    reason = str(normalized["reason"]).strip()
    if not reason:
        raise ManualTaskError("reason must be a non-empty string")

    completion_key = "completion_ref" if "completion_ref" in expected_outputs else "task_completion_ref"
    completion_ref = expected_outputs.get(completion_key)

    generated_refs: Dict[str, str] = {}
    for key, rel_path in expected_outputs.items():
        if key == completion_key:
            continue
        out_path = root / rel_path
        body = payload_map.get(key)
        if body is None:
            body = (
                f"# {key}\n"
                f"generated_at: {now_iso()}\n"
                f"objective_ref: {normalized['objective_ref']}\n"
                f"task_ref: {normalized['task_ref']}\n"
            )
        write_output_artifact(out_path, body)
        generated_refs[key] = rel_path

    if completion_ref:
        ensure_repo_rel_path(completion_ref, f"expected_outputs.{completion_key}")
        generated_refs[completion_key] = completion_ref

    evidence_ref = normalized.get("evidence_ref")
    if evidence_ref is None:
        if normalized["mode"] == "dispatch":
            dispatch = normalized["dispatch"]
            evidence_dir = str(dispatch.get("evidence_dir") or "").strip().rstrip("/")
            phase_id = str(dispatch.get("phase_id") or "phase")
            evidence_ref = f"{evidence_dir}/{phase_id}_manual_task_evidence.json"
        else:
            first_ref = next(iter(expected_outputs.values()))
            first_parent = Path(first_ref).parent
            evidence_ref = str(
                (first_parent / f"manual-task-evidence-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json").as_posix()
            )
    evidence_ref = ensure_repo_rel_path(str(evidence_ref), "evidence_ref")

    preferred_output_ref = generated_refs.get("output_ref")
    if preferred_output_ref is None:
        preferred_output_ref = next(iter(generated_refs.values()))

    completion_payload = None
    dispatch = normalized["dispatch"]
    if normalized["mode"] == "dispatch" and isinstance(dispatch, dict):
        binding = dispatch.get("session_binding", {})
        session_id = str(binding.get("session_id") or "").strip()
        completion_payload = {
            "type": "task_completion",
            "instance_id": dispatch.get("instance_id"),
            "phase_id": dispatch.get("phase_id"),
            "actor": dispatch.get("actor"),
            "lineage_ref": dispatch.get("lineage_ref"),
            "stack_depth": dispatch.get("stack_depth"),
            "session_id": session_id,
            "status": "completed" if decision == "pass" else "failed",
            "output_ref": preferred_output_ref,
            "evidence_ref": evidence_ref,
            "self_check": {
                "decision": decision,
                "reason": reason,
                "rule_refs": [DEFAULT_RULE_REF],
            },
        }
        if completion_ref:
            dump_json(root / completion_ref, completion_payload)

    evidence_payload = {
        "timestamp": now_iso(),
        "mode": normalized["mode"],
        "objective_ref": normalized["objective_ref"],
        "task_ref": normalized["task_ref"],
        "acceptance_criteria": normalized["acceptance_criteria"],
        "decision": decision,
        "reason": reason,
        "generated_refs": generated_refs,
    }
    if completion_payload is not None:
        evidence_payload["task_completion"] = completion_payload
    if isinstance(dispatch, dict):
        evidence_payload["dispatch"] = {
            "instance_id": dispatch.get("instance_id"),
            "phase_id": dispatch.get("phase_id"),
            "actor": dispatch.get("actor"),
            "target_id": dispatch.get("target_id"),
            "input_ref": dispatch.get("input_ref"),
            "objective_ref": dispatch.get("objective_ref"),
            "evidence_dir": dispatch.get("evidence_dir"),
        }
    dump_json(root / evidence_ref, evidence_payload)

    result = {
        "output_ref": preferred_output_ref,
        "evidence_ref": evidence_ref,
        "decision": decision,
        "reason": reason,
        "generated_refs": generated_refs,
        "mode": normalized["mode"],
    }
    if completion_ref:
        result["completion_ref"] = completion_ref
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute manual-task contract")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root()
    in_path = Path(args.input)
    if not in_path.is_absolute():
        in_path = root / in_path
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = root / out_path

    try:
        payload = load_json(in_path)
        result = run_manual_task(payload, root)
        dump_json(out_path, result)
        print(out_path.relative_to(root).as_posix())
        return 0
    except ManualTaskError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
