#!/usr/bin/env python3
"""Execute a structured manual task and emit standardized evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


REPO_REL_PATTERN = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$)).+")


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
        lines = []
        for item in payload:
            lines.append(json.dumps(item, ensure_ascii=False))
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


def validate_input(payload: Dict[str, Any], root: Path) -> None:
    required = ["objective_ref", "task_ref", "acceptance_criteria", "expected_outputs"]
    for key in required:
        if key not in payload:
            raise ManualTaskError(f"missing required field: {key}")

    task_ref = payload["task_ref"]
    ensure_repo_rel_path(task_ref, "task_ref")
    if not (root / task_ref).exists():
        raise ManualTaskError(f"task_ref not reachable: {task_ref}")

    acceptance = payload["acceptance_criteria"]
    if not isinstance(acceptance, str) or not acceptance.strip():
        raise ManualTaskError("acceptance_criteria must be a non-empty string")

    outputs = payload["expected_outputs"]
    if not isinstance(outputs, dict) or not outputs:
        raise ManualTaskError("expected_outputs must be a non-empty object")
    for key, path in outputs.items():
        if not isinstance(key, str) or not key.strip():
            raise ManualTaskError("expected_outputs keys must be non-empty strings")
        ensure_repo_rel_path(path, f"expected_outputs.{key}")


def run_manual_task(payload: Dict[str, Any], root: Path) -> Dict[str, Any]:
    validate_input(payload, root)

    expected_outputs: Dict[str, str] = payload["expected_outputs"]
    payload_map = payload.get("payload", {})
    if payload_map is None:
        payload_map = {}
    if not isinstance(payload_map, dict):
        raise ManualTaskError("payload must be an object when provided")

    generated_refs: Dict[str, str] = {}
    for key, rel_path in expected_outputs.items():
        out_path = root / rel_path
        body = payload_map.get(key)
        if body is None:
            body = (
                f"# {key}\n"
                f"generated_at: {now_iso()}\n"
                f"objective_ref: {payload['objective_ref']}\n"
                f"task_ref: {payload['task_ref']}\n"
            )
        write_output_artifact(out_path, body)
        generated_refs[key] = rel_path

    evidence_ref = payload.get("evidence_ref")
    if evidence_ref is None:
        first_ref = next(iter(expected_outputs.values()))
        first_parent = Path(first_ref).parent
        evidence_ref = str((first_parent / f"manual-task-evidence-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json").as_posix())
    evidence_ref = ensure_repo_rel_path(evidence_ref, "evidence_ref")

    decision = payload.get("decision", "pass")
    if decision not in {"pass", "fail"}:
        raise ManualTaskError("decision must be pass or fail")

    reason = payload.get("reason", "manual task completed")
    if not isinstance(reason, str) or not reason.strip():
        raise ManualTaskError("reason must be a non-empty string")

    evidence_payload = {
        "timestamp": now_iso(),
        "objective_ref": payload["objective_ref"],
        "task_ref": payload["task_ref"],
        "acceptance_criteria": payload["acceptance_criteria"],
        "decision": decision,
        "reason": reason,
        "generated_refs": generated_refs,
    }
    dump_json(root / evidence_ref, evidence_payload)

    preferred_output_ref = generated_refs.get("output_ref")
    if preferred_output_ref is None:
        preferred_output_ref = next(iter(generated_refs.values()))

    result = {
        "output_ref": preferred_output_ref,
        "evidence_ref": evidence_ref,
        "decision": decision,
        "reason": reason,
        "generated_refs": generated_refs,
    }
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute manual task contract")
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
