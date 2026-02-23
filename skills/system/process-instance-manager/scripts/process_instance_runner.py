#!/usr/bin/env python3
"""Executable runner for sys.bpm.process-instance-manager.

Commands:
- start: create one process instance with strict session binding.
- migrate: migrate legacy state.json instances to context.json + session_binding.json.
- validate: validate all instance context/session schema constraints.
- replay: verify phase replay transitions against process control_flow.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_REL_RE = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$)).+")
ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class RunnerError(RuntimeError):
    """Fail-closed runner error."""


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
        raise RunnerError("not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RunnerError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RunnerError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RunnerError(f"json root must be object: {path}")
    return payload


def ensure_repo_rel(path: str, field: str) -> str:
    if not isinstance(path, str) or REPO_REL_RE.match(path) is None:
        raise RunnerError(f"{field} must be repo-relative path without '..': {path!r}")
    return path


def resolve_instance_root(root: Path, raw: Optional[str]) -> Path:
    if not raw:
        return root / "agents/control/BPM/memory/process_instances"
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate
    return (root / raw).resolve()


def normalize_status(raw: Any) -> str:
    status = str(raw or "").strip().lower()
    mapping = {
        "created": "created",
        "running": "running",
        "waiting": "waiting",
        "completed": "completed",
        "failed": "failed",
        "cancelled": "cancelled",
        "archived": "archived",
        "complete": "completed",
        "fail": "failed",
    }
    return mapping.get(status, "failed")


def normalize_phase_status(raw: Any) -> str:
    status = str(raw or "").strip().lower()
    mapping = {
        "running": "running",
        "completed": "completed",
        "failed": "failed",
        "hold": "hold",
        "escalated": "escalate",
        "escalate": "escalate",
        "skipped": "skipped",
        "skip": "skipped",
        "complete": "completed",
        "success": "completed",
        "pass": "completed",
        "fail": "failed",
    }
    return mapping.get(status, "failed")


def generate_instance_id(process_id: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"run-{process_id}-{stamp}-{uuid.uuid4().hex[:4]}"


def generate_session_id() -> str:
    return f"sess-{uuid.uuid4().hex[:16]}"


def load_process_registry(root: Path) -> Dict[str, Dict[str, Any]]:
    payload = load_json(root / "shared/registry/process_registry.json")
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        raise RunnerError("process_registry.entries must be array")
    index: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("process_id"), str):
            index[entry["process_id"]] = entry
    return index


def load_process_manifest(root: Path, process_id: str) -> Dict[str, Any]:
    registry = load_process_registry(root)
    entry = registry.get(process_id)
    if entry is None:
        raise RunnerError(f"unregistered process_id: {process_id}")

    manifest_rel = entry.get("manifest_path")
    if not isinstance(manifest_rel, str) or REPO_REL_RE.match(manifest_rel) is None:
        raise RunnerError(f"invalid manifest_path for process {process_id!r}: {manifest_rel!r}")

    manifest = load_json(root / manifest_rel)
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: Dict[str, Any]) -> None:
    required = ["process_id", "version", "process_level", "phases", "control_flow", "lineage_policy"]
    for key in required:
        if key not in manifest:
            raise RunnerError(f"process manifest missing field: {key}")

    phases = manifest.get("phases")
    if not isinstance(phases, list) or not phases:
        raise RunnerError("process manifest phases must be non-empty array")

    phase_ids: List[str] = []
    for idx, phase in enumerate(phases):
        if not isinstance(phase, dict):
            raise RunnerError(f"phases[{idx}] must be object")
        for key in ["phase_id", "actor", "target_type", "target_id"]:
            if key not in phase:
                raise RunnerError(f"phases[{idx}] missing field: {key}")
        phase_id = phase["phase_id"]
        if not isinstance(phase_id, str) or not phase_id:
            raise RunnerError(f"phases[{idx}].phase_id must be non-empty string")
        phase_ids.append(phase_id)

    control_flow = manifest.get("control_flow")
    if not isinstance(control_flow, list) or not control_flow:
        raise RunnerError("process manifest control_flow must be non-empty array")

    allowed_edge_on = {"success", "failure", "hold", "escalate", "skip"}
    linked_ids: set[str] = set()
    for idx, edge in enumerate(control_flow):
        if not isinstance(edge, dict):
            raise RunnerError(f"control_flow[{idx}] must be object")
        for key in ["from", "to", "on"]:
            if key not in edge:
                raise RunnerError(f"control_flow[{idx}] missing field: {key}")

        edge_from = edge.get("from")
        edge_to = edge.get("to")
        edge_on = edge.get("on")
        if edge_on not in allowed_edge_on:
            allowed_text = "|".join(sorted(allowed_edge_on))
            raise RunnerError(f"control_flow[{idx}].on must be {allowed_text}")

        if edge_from not in phase_ids:
            raise RunnerError(f"control_flow[{idx}].from invalid phase_id: {edge_from!r}")
        if edge_to != "end" and edge_to not in phase_ids:
            raise RunnerError(f"control_flow[{idx}].to invalid phase_id: {edge_to!r}")

        linked_ids.add(str(edge_from))
        if edge_to != "end":
            linked_ids.add(str(edge_to))

    for phase_id in phase_ids:
        if phase_id not in linked_ids:
            raise RunnerError(f"phase closure violation, unlinked phase: {phase_id}")


def phase_by_id(manifest: Dict[str, Any], phase_id: str) -> Dict[str, Any]:
    for phase in manifest["phases"]:
        if phase.get("phase_id") == phase_id:
            return phase
    raise RunnerError(f"phase not found in manifest: {phase_id}")


def read_instance_record(instance_root: Path, instance_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    instance_dir = instance_root / instance_id
    context = load_json(instance_dir / "context.json")
    binding = load_json(instance_dir / "session_binding.json")
    return context, binding


def build_dispatch_command(
    openclaw_bin: str,
    actor: str,
    session_id: str,
    message: str,
    timeout_seconds: int,
) -> List[str]:
    if not session_id:
        raise RunnerError("session_id is required for dispatch command")
    return [
        openclaw_bin,
        "agent",
        "--agent",
        actor,
        "--session-id",
        session_id,
        "--timeout",
        str(timeout_seconds),
        "--message",
        message,
        "--json",
    ]


def run_dispatch(command: List[str]) -> Dict[str, Any]:
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "return_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def parse_first_json_object(text: str) -> Dict[str, Any]:
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(text):
        ch = text[idx]
        if ch != "{":
            idx += 1
            continue
        try:
            obj, _ = decoder.raw_decode(text, idx)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
        idx += 1
    raise RunnerError("unable to parse json object from command stdout")


def reset_openclaw_session(openclaw_bin: str, actor: str) -> Dict[str, Any]:
    session_key = f"agent:{actor}:main"
    params = json.dumps({"key": session_key}, ensure_ascii=True)
    cmd = [
        openclaw_bin,
        "gateway",
        "call",
        "sessions.reset",
        "--params",
        params,
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RunnerError(
            "openclaw_session_reset_failed:"
            f"actor={actor}:rc={proc.returncode}:stderr={proc.stderr.strip()}"
        )
    payload = parse_first_json_object(proc.stdout)
    if not bool(payload.get("ok")):
        raise RunnerError(f"openclaw_session_reset_rejected:actor={actor}")
    entry = payload.get("entry")
    if not isinstance(entry, dict):
        raise RunnerError(f"openclaw_session_reset_missing_entry:actor={actor}")
    session_id = str(entry.get("sessionId") or "").strip()
    if not session_id:
        raise RunnerError(f"openclaw_session_reset_missing_session_id:actor={actor}")
    return {
        "key": session_key,
        "session_id": session_id,
        "updated_at": entry.get("updatedAt"),
    }


def extract_actual_session_id(stdout: str) -> str:
    try:
        payload = parse_first_json_object(stdout)
    except RunnerError:
        return ""
    result = payload.get("result")
    if not isinstance(result, dict):
        return ""
    meta = result.get("meta")
    if not isinstance(meta, dict):
        return ""
    agent_meta = meta.get("agentMeta")
    if not isinstance(agent_meta, dict):
        return ""
    return str(agent_meta.get("sessionId") or "").strip()


def parse_legacy_context_md(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        striped = line.strip()
        if striped.startswith("- ") and ":" in striped:
            key, value = striped[2:].split(":", 1)
            out[key.strip()] = value.strip()
    return out


def collect_required_field_errors(context: Dict[str, Any], binding: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    top_required = [
        "instance_id",
        "session_binding",
        "lineage_ref",
        "stack_depth",
        "process_id",
        "process_version",
        "process_level",
        "status",
        "created_at",
        "updated_at",
        "phase_results",
    ]
    for key in top_required:
        if key not in context:
            errors.append(f"missing_context_field:{key}")

    if not isinstance(context.get("session_binding"), dict):
        errors.append("session_binding_not_object")
    else:
        for key in ["agent_id", "session_key", "session_id", "parent_session_id"]:
            if key not in context["session_binding"]:
                errors.append(f"missing_session_binding_field:{key}")

    if not isinstance(binding, dict):
        errors.append("session_binding_file_not_object")
    else:
        for key in ["agent_id", "session_key", "session_id", "parent_session_id"]:
            if key not in binding:
                errors.append(f"missing_session_binding_file_field:{key}")

    if isinstance(context.get("phase_results"), list):
        for idx, item in enumerate(context["phase_results"]):
            if not isinstance(item, dict):
                errors.append(f"phase_results[{idx}]_not_object")
                continue
            for key in ["phase_id", "status", "actor", "session_id"]:
                if key not in item:
                    errors.append(f"missing_phase_result_field:{idx}:{key}")

    if isinstance(context.get("stack_depth"), int):
        stack_depth = int(context["stack_depth"])
        parent_instance_id = context.get("parent_instance_id")
        parent_session_id = None
        session_binding = context.get("session_binding")
        if isinstance(session_binding, dict):
            parent_session_id = session_binding.get("parent_session_id")
            session_id = session_binding.get("session_id")
            if session_id and parent_session_id and session_id == parent_session_id:
                errors.append("session_reuses_parent")

        if stack_depth == 0:
            if parent_instance_id is not None:
                errors.append("root_has_parent_instance")
            if parent_session_id not in (None, ""):
                errors.append("root_has_parent_session")
        else:
            if not parent_instance_id:
                errors.append("child_missing_parent_instance")
            if not parent_session_id:
                errors.append("child_missing_parent_session")
    else:
        errors.append("stack_depth_not_integer")

    if context.get("session_binding") != binding:
        errors.append("session_binding_mismatch")

    for key in ["created_at", "updated_at"]:
        value = context.get(key)
        if not isinstance(value, str) or ISO_Z_RE.match(value) is None:
            errors.append(f"invalid_iso_time:{key}")

    return errors


def validate_context_against_manifest(context: Dict[str, Any], manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    process_id = context.get("process_id")
    if process_id != manifest.get("process_id"):
        errors.append("process_id_mismatch")

    phase_ids = {phase["phase_id"] for phase in manifest.get("phases", []) if isinstance(phase, dict)}
    for idx, phase_result in enumerate(context.get("phase_results", [])):
        if phase_result.get("phase_id") not in phase_ids:
            errors.append(f"unknown_phase_in_result:{idx}:{phase_result.get('phase_id')}")

    return errors


def replay_errors(context: Dict[str, Any], manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    phase_results = context.get("phase_results", [])
    if not isinstance(phase_results, list) or not phase_results:
        errors.append("empty_phase_results")
        return errors

    allowed_edges = set()
    for edge in manifest.get("control_flow", []):
        if not isinstance(edge, dict):
            continue
        allowed_edges.add((edge.get("from"), edge.get("to"), edge.get("on")))

    for idx, current in enumerate(phase_results[:-1]):
        nxt = phase_results[idx + 1]
        from_phase = current.get("phase_id")
        to_phase = nxt.get("phase_id")
        current_status = normalize_phase_status(current.get("status"))
        transition_on = str(current.get("transition_on") or "").strip().lower()
        if transition_on:
            edge_on = transition_on
        elif current_status == "failed":
            edge_on = "failure"
        elif current_status == "hold":
            edge_on = "hold"
        elif current_status == "escalate":
            edge_on = "escalate"
        elif current_status == "skipped":
            edge_on = "skip"
        else:
            edge_on = "success"
        if (from_phase, to_phase, edge_on) not in allowed_edges:
            errors.append(f"illegal_transition:{from_phase}->{to_phase}:{edge_on}")

    used_sessions: set[str] = set()
    for idx, item in enumerate(phase_results):
        session_id = item.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            errors.append(f"missing_phase_session:{idx}")
            continue
        if session_id in used_sessions:
            errors.append(f"duplicated_phase_session:{session_id}")
        used_sessions.add(session_id)

    return errors


def start_command(args: argparse.Namespace) -> int:
    root = repo_root()
    instance_root = resolve_instance_root(root, args.instance_root)
    instance_root.mkdir(parents=True, exist_ok=True)

    manifest = load_process_manifest(root, args.process_id)
    phase = phase_by_id(manifest, args.phase_id)

    parent_context: Optional[Dict[str, Any]] = None
    parent_binding: Optional[Dict[str, Any]] = None
    if args.parent_instance_id:
        parent_context, parent_binding = read_instance_record(instance_root, args.parent_instance_id)

    expected_depth = 0
    parent_instance_id: Optional[str] = None
    parent_session_id: Optional[str] = None
    if parent_context is not None and parent_binding is not None:
        parent_instance_id = str(parent_context.get("instance_id"))
        if not isinstance(parent_context.get("stack_depth"), int):
            raise RunnerError("parent stack_depth must be integer")
        expected_depth = int(parent_context["stack_depth"]) + 1
        parent_session_id = parent_binding.get("session_id")

    if args.stack_depth is None:
        stack_depth = expected_depth
    else:
        stack_depth = int(args.stack_depth)
    if stack_depth != expected_depth:
        raise RunnerError(f"invalid_stack_depth: expected {expected_depth}, got {stack_depth}")

    instance_id = args.instance_id or generate_instance_id(args.process_id)
    instance_dir = instance_root / instance_id
    if instance_dir.exists():
        raise RunnerError(f"instance already exists: {instance_id}")
    instance_dir.mkdir(parents=True, exist_ok=False)

    actor = str(phase.get("actor"))
    session_key = args.session_key or f"{args.process_id}:{args.phase_id}:{uuid.uuid4().hex[:8]}"
    session_id = args.session_id or generate_session_id()
    session_reset: Optional[Dict[str, Any]] = None
    if args.execute_openclaw and args.reset_openclaw_session:
        session_reset = reset_openclaw_session(args.openclaw_bin, actor)
        session_id = session_reset["session_id"]
    if parent_session_id and session_id == parent_session_id:
        raise RunnerError("session_reuses_parent")

    lineage_ref = args.lineage_ref
    if not lineage_ref:
        if parent_context is None:
            lineage_ref = f"lineage/{instance_id}"
        else:
            lineage_ref = f"{parent_context.get('lineage_ref', 'lineage/unknown')}/{instance_id}"

    ts = now_iso()
    binding = {
        "agent_id": actor,
        "session_key": session_key,
        "session_id": session_id,
        "parent_session_id": parent_session_id,
    }

    context = {
        "instance_id": instance_id,
        "parent_instance_id": parent_instance_id,
        "session_binding": binding,
        "lineage_ref": lineage_ref,
        "stack_depth": stack_depth,
        "process_id": manifest["process_id"],
        "process_version": manifest["version"],
        "process_level": manifest["process_level"],
        "objective_ref": args.objective_ref or str(manifest.get("objective_ref", "")),
        "initiated_by": args.initiated_by,
        "status": "running",
        "created_at": ts,
        "updated_at": ts,
        "current_phase": args.phase_id,
        "phase_results": [
            {
                "phase_id": args.phase_id,
                "status": "running",
                "actor": actor,
                "session_id": session_id,
                "input_ref": args.input_ref,
                "output_ref": "",
                "started_at": ts,
                "completed_at": "",
            }
        ],
    }

    errors = collect_required_field_errors(context, binding)
    errors.extend(validate_context_against_manifest(context, manifest))
    if errors:
        raise RunnerError(";".join(errors))

    context_ref = instance_dir / "context.json"
    binding_ref = instance_dir / "session_binding.json"
    transition_ref = instance_dir / "evidence" / "state_transition_start.json"

    dump_json(context_ref, context)
    dump_json(binding_ref, binding)
    dump_json(
        transition_ref,
        {
            "timestamp": ts,
            "event": "instance_started",
            "instance_id": instance_id,
            "phase_id": args.phase_id,
            "session_id": session_id,
            "actor": actor,
            "lineage_ref": lineage_ref,
            "stack_depth": stack_depth,
        },
    )

    command = build_dispatch_command(
        args.openclaw_bin,
        actor,
        session_id,
        args.dispatch_message,
        args.openclaw_timeout_seconds,
    )
    dispatch_result: Dict[str, Any] = {
        "executed": False,
        "command": command,
        "return_code": None,
        "stdout": "",
        "stderr": "",
        "actual_session_id": "",
        "session_reset": session_reset,
    }

    if args.execute_openclaw:
        proc_result = run_dispatch(command)
        actual_session_id = extract_actual_session_id(proc_result["stdout"])
        dispatch_result.update(
            {
                "executed": True,
                "return_code": proc_result["return_code"],
                "stdout": proc_result["stdout"],
                "stderr": proc_result["stderr"],
                "actual_session_id": actual_session_id,
            }
        )
        if args.strict_session_match and actual_session_id and actual_session_id != session_id:
            raise RunnerError(
                "openclaw_session_mismatch:"
                f"expected={session_id}:actual={actual_session_id}:actor={actor}"
            )

    result = {
        "status": "ok",
        "instance_id": instance_id,
        "context_ref": str(context_ref.relative_to(root).as_posix()),
        "session_binding_ref": str(binding_ref.relative_to(root).as_posix()),
        "state_transition_ref": str(transition_ref.relative_to(root).as_posix()),
        "runtime_state": "running",
        "dispatch": dispatch_result,
        "evidence_ref": str((instance_dir / "evidence").relative_to(root).as_posix()),
    }

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = root / output_path
        dump_json(output_path, result)

    print(json.dumps(result, ensure_ascii=False))
    return 0


def migrate_one_instance(root: Path, instance_root: Path, manifest: Dict[str, Any], instance_dir: Path) -> Dict[str, Any]:
    state = load_json(instance_dir / "state.json")
    context_md = parse_legacy_context_md(instance_dir / "context.md")

    instance_id = str(state.get("instance_id") or instance_dir.name)
    process_id = str(state.get("process_id") or manifest.get("process_id"))
    current_phase = str(state.get("current_phase") or "")
    actor_map = {
        str(phase.get("phase_id")): str(phase.get("actor"))
        for phase in manifest.get("phases", [])
        if isinstance(phase, dict)
    }

    started_at = str(state.get("started_at") or now_iso())
    finished_at = str(state.get("finished_at") or started_at)
    session_id = f"legacy-{instance_id}-{current_phase or 'root'}"

    history = state.get("history")
    if not isinstance(history, list):
        history = []

    phase_results: List[Dict[str, Any]] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        phase_id = str(item.get("phase_id") or "")
        if not phase_id:
            continue
        phase_results.append(
            {
                "phase_id": phase_id,
                "status": normalize_phase_status(item.get("state")),
                "actor": actor_map.get(phase_id, "unknown"),
                "session_id": f"legacy-{instance_id}-{phase_id}",
                "input_ref": f"agents/control/BPM/memory/process_instances/{instance_id}/evidence/{phase_id}/input.md",
                "output_ref": f"agents/control/BPM/memory/process_instances/{instance_id}/evidence/{phase_id}/output.md",
                "started_at": started_at,
                "completed_at": finished_at,
            }
        )

    if not phase_results and current_phase:
        phase_results.append(
            {
                "phase_id": current_phase,
                "status": "completed" if normalize_status(state.get("state")) == "completed" else "failed",
                "actor": actor_map.get(current_phase, "unknown"),
                "session_id": session_id,
                "input_ref": "",
                "output_ref": "",
                "started_at": started_at,
                "completed_at": finished_at,
            }
        )

    context = {
        "instance_id": instance_id,
        "parent_instance_id": None,
        "session_binding": {
            "agent_id": actor_map.get(current_phase, "bpm"),
            "session_key": f"legacy:{instance_id}:{current_phase or 'root'}",
            "session_id": session_id,
            "parent_session_id": None,
        },
        "lineage_ref": f"legacy/{instance_id}",
        "stack_depth": 0,
        "process_id": process_id,
        "process_version": str(manifest.get("version", "0.0.0")),
        "process_level": str(manifest.get("process_level", "P4")),
        "objective_ref": context_md.get("objective_ref", str(manifest.get("objective_ref", "legacy-objective"))),
        "initiated_by": context_md.get("initiator", "legacy"),
        "status": normalize_status(state.get("state")),
        "created_at": started_at,
        "updated_at": finished_at,
        "current_phase": current_phase,
        "phase_results": phase_results,
    }

    binding = context["session_binding"]
    errors = collect_required_field_errors(context, binding)
    errors.extend(validate_context_against_manifest(context, manifest))
    errors.extend(replay_errors(context, manifest))
    if errors:
        raise RunnerError(";".join(errors))

    dump_json(instance_dir / "context.json", context)
    dump_json(instance_dir / "session_binding.json", binding)

    return {
        "instance_id": instance_id,
        "status": "migrated",
        "reason": "ok",
    }


def migrate_command(args: argparse.Namespace) -> int:
    root = repo_root()
    instance_root = resolve_instance_root(root, args.instance_root)
    if not instance_root.exists():
        raise RunnerError(f"instance_root not found: {instance_root}")

    report: Dict[str, Any] = {
        "ts": now_iso(),
        "instance_root": str(instance_root),
        "total": 0,
        "migrated": 0,
        "validated_existing": 0,
        "failed": 0,
        "results": [],
    }

    for instance_dir in sorted([p for p in instance_root.iterdir() if p.is_dir()]):
        report["total"] += 1
        instance_id = instance_dir.name
        context_path = instance_dir / "context.json"
        binding_path = instance_dir / "session_binding.json"
        state_path = instance_dir / "state.json"

        try:
            if context_path.exists() and binding_path.exists():
                context = load_json(context_path)
                binding = load_json(binding_path)
                manifest = load_process_manifest(root, str(context.get("process_id")))
                errors = collect_required_field_errors(context, binding)
                errors.extend(validate_context_against_manifest(context, manifest))
                errors.extend(replay_errors(context, manifest))
                if errors:
                    raise RunnerError(";".join(errors))
                report["validated_existing"] += 1
                report["results"].append(
                    {"instance_id": instance_id, "status": "validated_existing", "reason": "ok"}
                )
                continue

            if not state_path.exists():
                raise RunnerError("missing_state_json")

            state = load_json(state_path)
            process_id = str(state.get("process_id") or "")
            if not process_id:
                raise RunnerError("legacy_state_missing_process_id")
            manifest = load_process_manifest(root, process_id)
            migrated = migrate_one_instance(root, instance_root, manifest, instance_dir)
            report["migrated"] += 1
            report["results"].append(migrated)
        except Exception as exc:
            report["failed"] += 1
            report["results"].append(
                {
                    "instance_id": instance_id,
                    "status": "failed",
                    "reason": str(exc),
                }
            )

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path
    dump_json(output_path, report)

    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["failed"] == 0 else 2


def validate_command(args: argparse.Namespace) -> int:
    root = repo_root()
    instance_root = resolve_instance_root(root, args.instance_root)
    if not instance_root.exists():
        raise RunnerError(f"instance_root not found: {instance_root}")

    details: List[Dict[str, Any]] = []
    pass_count = 0
    fail_count = 0

    for instance_dir in sorted([p for p in instance_root.iterdir() if p.is_dir()]):
        context_path = instance_dir / "context.json"
        binding_path = instance_dir / "session_binding.json"

        if not context_path.exists() or not binding_path.exists():
            fail_count += 1
            details.append(
                {
                    "instance_id": instance_dir.name,
                    "status": "fail",
                    "errors": ["missing_context_or_binding"],
                }
            )
            continue

        context = load_json(context_path)
        binding = load_json(binding_path)
        errors = collect_required_field_errors(context, binding)
        try:
            manifest = load_process_manifest(root, str(context.get("process_id")))
            errors.extend(validate_context_against_manifest(context, manifest))
        except Exception as exc:
            errors.append(f"manifest_error:{exc}")

        if errors:
            fail_count += 1
            details.append(
                {
                    "instance_id": instance_dir.name,
                    "status": "fail",
                    "errors": errors,
                }
            )
        else:
            pass_count += 1
            details.append(
                {
                    "instance_id": instance_dir.name,
                    "status": "pass",
                    "errors": [],
                }
            )

    report = {
        "ts": now_iso(),
        "instance_root": str(instance_root),
        "total": pass_count + fail_count,
        "passed": pass_count,
        "failed": fail_count,
        "pass_rate": 1.0 if (pass_count + fail_count == 0) else pass_count / float(pass_count + fail_count),
        "details": details,
    }

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path
    dump_json(output_path, report)

    print(json.dumps(report, ensure_ascii=False))
    return 0 if fail_count == 0 else 2


def replay_command(args: argparse.Namespace) -> int:
    root = repo_root()
    instance_root = resolve_instance_root(root, args.instance_root)
    if not instance_root.exists():
        raise RunnerError(f"instance_root not found: {instance_root}")

    pass_count = 0
    fail_count = 0
    details: List[Dict[str, Any]] = []

    for instance_dir in sorted([p for p in instance_root.iterdir() if p.is_dir()]):
        context_path = instance_dir / "context.json"
        binding_path = instance_dir / "session_binding.json"
        if not context_path.exists() or not binding_path.exists():
            fail_count += 1
            details.append(
                {
                    "instance_id": instance_dir.name,
                    "status": "fail",
                    "errors": ["missing_context_or_binding"],
                }
            )
            continue

        context = load_json(context_path)
        binding = load_json(binding_path)
        errors = collect_required_field_errors(context, binding)

        try:
            manifest = load_process_manifest(root, str(context.get("process_id")))
            errors.extend(validate_context_against_manifest(context, manifest))
            errors.extend(replay_errors(context, manifest))
        except Exception as exc:
            errors.append(f"manifest_or_replay_error:{exc}")

        if errors:
            fail_count += 1
            details.append(
                {
                    "instance_id": instance_dir.name,
                    "status": "fail",
                    "errors": errors,
                }
            )
        else:
            pass_count += 1
            details.append(
                {
                    "instance_id": instance_dir.name,
                    "status": "pass",
                    "errors": [],
                }
            )

    report = {
        "ts": now_iso(),
        "instance_root": str(instance_root),
        "total": pass_count + fail_count,
        "passed": pass_count,
        "failed": fail_count,
        "details": details,
    }

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path
    dump_json(output_path, report)

    print(json.dumps(report, ensure_ascii=False))
    return 0 if fail_count == 0 else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="sys.bpm.process-instance-manager executable runner")
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="create new process instance")
    p_start.add_argument("--process-id", required=True)
    p_start.add_argument("--phase-id", required=True)
    p_start.add_argument("--instance-root")
    p_start.add_argument("--instance-id")
    p_start.add_argument("--parent-instance-id")
    p_start.add_argument("--lineage-ref")
    p_start.add_argument("--stack-depth", type=int)
    p_start.add_argument("--session-key")
    p_start.add_argument("--session-id")
    p_start.add_argument("--objective-ref")
    p_start.add_argument("--initiated-by", default="bpm")
    p_start.add_argument("--input-ref", default="")
    p_start.add_argument("--dispatch-message", default="execute assigned phase by process-instance-manager contract")
    p_start.add_argument("--openclaw-bin", default="openclaw")
    p_start.add_argument(
        "--openclaw-timeout-seconds",
        type=int,
        default=120,
        help="Timeout seconds passed to `openclaw agent --timeout`",
    )
    p_start.add_argument("--execute-openclaw", action="store_true")
    p_start.add_argument(
        "--reset-openclaw-session",
        action="store_true",
        help="Reset agent session via `openclaw gateway call sessions.reset` before dispatch",
    )
    p_start.add_argument(
        "--strict-session-match",
        action="store_true",
        help="Fail when dispatch returned agent session id mismatches context session id",
    )
    p_start.add_argument("--output")

    p_migrate = sub.add_parser("migrate", help="migrate legacy state.json to new schema")
    p_migrate.add_argument("--instance-root")
    p_migrate.add_argument("--output", required=True)

    p_validate = sub.add_parser("validate", help="validate instance schema")
    p_validate.add_argument("--instance-root")
    p_validate.add_argument("--output", required=True)

    p_replay = sub.add_parser("replay", help="validate replay transitions")
    p_replay.add_argument("--instance-root")
    p_replay.add_argument("--output", required=True)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "start":
            return start_command(args)
        if args.command == "migrate":
            return migrate_command(args)
        if args.command == "validate":
            return validate_command(args)
        if args.command == "replay":
            return replay_command(args)
        raise RunnerError(f"unsupported command: {args.command}")
    except RunnerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
