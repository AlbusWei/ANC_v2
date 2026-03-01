#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

EXIT_SUCCESS = 0
EXIT_UNEXPECTED_ERROR = 1
EXIT_FAIL_CLOSED = 2

PROCESS_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VALID_PROCESS_LEVELS = {"p1", "p2", "p3", "p4", "p5", "p6"}
CONTROL_EDGE_ON = {"success", "failure", "hold", "escalate", "skip"}
REPO_REL_ANCHOR_RE = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$)).+#[^#]+$")

REQUIRED_TOP_LEVEL_FIELDS = [
    "process_id",
    "version",
    "process_level",
    "phases",
    "control_flow",
    "fail_policy",
    "evidence_policy",
    "lineage_policy",
]

REQUIRED_PHASE_FIELDS = [
    "phase_id",
    "name",
    "actor",
    "target_type",
    "target_id",
    "requires_spec",
    "sipoc",
    "acceptance_criteria",
    "phase_purpose",
    "input_context_ref",
    "done_definition",
    "handoff_note",
]

REQUIRED_INLINE_AP_FIELDS = ["ap_id", "skill_id", "actor", "pierce_allowed"]
LEGACY_FORBIDDEN_FIELDS = ["control", "failure_policy"]
COLLABORATION_POLICY_REQUIRED_FIELDS = ["mode", "dispatch_runtime", "session_reset"]


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError("输入 JSON 根对象必须是 object")
    return payload


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("not inside git repository")
    return Path(proc.stdout.strip()).resolve()


def load_registry_ids(root: Path) -> tuple[Set[str], Set[str]]:
    process_registry_path = root / "shared/registry/process_registry.json"
    skill_registry_path = root / "shared/registry/skill_registry.json"

    process_payload = read_json(process_registry_path)
    skill_payload = read_json(skill_registry_path)

    process_ids: Set[str] = set()
    for entry in process_payload.get("entries", []):
        if isinstance(entry, dict) and isinstance(entry.get("process_id"), str):
            process_ids.add(entry["process_id"])

    skill_ids: Set[str] = set()
    for entry in skill_payload.get("entries", []):
        if isinstance(entry, dict) and isinstance(entry.get("skill_id"), str):
            skill_ids.add(entry["skill_id"])

    return process_ids, skill_ids


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
                "runner": "process_creator_runner",
                "decision": "fail_closed",
                "reason_code": reason_code,
                "details": details,
            },
        )
    return EXIT_FAIL_CLOSED


def validate_top_level(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    missing = [field for field in REQUIRED_TOP_LEVEL_FIELDS if field not in data]
    if missing:
        errors.append(f"missing_required_fields:{','.join(missing)}")

    for forbidden in LEGACY_FORBIDDEN_FIELDS:
        if forbidden in data:
            errors.append(f"legacy_field_forbidden:{forbidden}")

    process_id = str(data.get("process_id") or "").strip()
    if not PROCESS_ID_PATTERN.fullmatch(process_id):
        errors.append("invalid_process_id")

    process_level = str(data.get("process_level") or "").strip().lower()
    if process_level not in VALID_PROCESS_LEVELS:
        errors.append("invalid_process_level")

    version = str(data.get("version") or "").strip()
    if not re.match(r"^[0-9]+\.[0-9]+\.[0-9]+$", version):
        errors.append("invalid_version_semver")

    return errors


def validate_phase(
    *,
    phase: Dict[str, Any],
    index: int,
    process_ids: Set[str],
    skill_ids: Set[str],
) -> List[str]:
    errors: List[str] = []
    prefix = f"phase[{index}]"

    for field in REQUIRED_PHASE_FIELDS:
        if field not in phase:
            errors.append(f"{prefix}:missing_{field}")

    target_type = str(phase.get("target_type") or "")
    if target_type != "subprocess":
        errors.append(f"{prefix}:target_type_must_be_subprocess")

    requires_spec = phase.get("requires_spec")
    if not isinstance(requires_spec, bool):
        errors.append(f"{prefix}:requires_spec_must_be_boolean")
    elif requires_spec:
        spec_ref = str(phase.get("spec_ref") or "").strip()
        if not spec_ref:
            errors.append(f"{prefix}:missing_spec_ref")
        elif REPO_REL_ANCHOR_RE.match(spec_ref) is None:
            errors.append(f"{prefix}:invalid_spec_ref_anchor")

    target_id = str(phase.get("target_id") or "").strip()
    if not target_id:
        errors.append(f"{prefix}:missing_target_id")
        return errors

    if target_id in process_ids:
        if "inline_ap" in phase:
            errors.append(f"{prefix}:registered_subprocess_must_not_define_inline_ap")
        return errors

    inline_ap = phase.get("inline_ap")
    if not isinstance(inline_ap, dict):
        errors.append(f"{prefix}:inline_ap_required_for_unregistered_target")
        return errors

    for field in REQUIRED_INLINE_AP_FIELDS:
        if field not in inline_ap:
            errors.append(f"{prefix}:inline_ap_missing_{field}")

    ap_id = str(inline_ap.get("ap_id") or "").strip()
    if ap_id != target_id:
        errors.append(f"{prefix}:inline_ap_id_must_equal_target_id")

    skill_id = str(inline_ap.get("skill_id") or "").strip()
    if skill_id not in skill_ids:
        errors.append(f"{prefix}:inline_ap_skill_not_found:{skill_id}")

    inline_actor = str(inline_ap.get("actor") or "").strip()
    phase_actor = str(phase.get("actor") or "").strip()
    if not inline_actor:
        errors.append(f"{prefix}:inline_ap_actor_required")

    pierce_allowed = inline_ap.get("pierce_allowed")
    if not isinstance(pierce_allowed, bool):
        errors.append(f"{prefix}:inline_ap_pierce_allowed_must_be_boolean")
    elif pierce_allowed and inline_actor != phase_actor:
        errors.append(f"{prefix}:inline_ap_pierce_actor_mismatch")

    return errors


def validate_phases(
    *,
    data: Dict[str, Any],
    process_ids: Set[str],
    skill_ids: Set[str],
) -> tuple[List[str], Set[str]]:
    errors: List[str] = []
    phase_ids: Set[str] = set()

    phases = data.get("phases")
    if not isinstance(phases, list) or not phases:
        return ["invalid_phases"], phase_ids

    for index, phase in enumerate(phases):
        if not isinstance(phase, dict):
            errors.append(f"phase[{index}]:not_object")
            continue

        phase_id = str(phase.get("phase_id") or "").strip()
        if phase_id:
            if phase_id in phase_ids:
                errors.append(f"phase[{index}]:duplicate_phase_id:{phase_id}")
            phase_ids.add(phase_id)

        errors.extend(
            validate_phase(
                phase=phase,
                index=index,
                process_ids=process_ids,
                skill_ids=skill_ids,
            )
        )

    return errors, phase_ids


def validate_control_flow(data: Dict[str, Any], phase_ids: Set[str]) -> List[str]:
    errors: List[str] = []
    control_flow = data.get("control_flow")
    if not isinstance(control_flow, list) or not control_flow:
        return ["invalid_control_flow"]

    linked = set()
    has_terminal = False
    for index, edge in enumerate(control_flow):
        if not isinstance(edge, dict):
            errors.append(f"control_flow[{index}]:not_object")
            continue

        for field in ("from", "to", "on"):
            if field not in edge:
                errors.append(f"control_flow[{index}]:missing_{field}")

        from_phase = str(edge.get("from") or "").strip()
        to_phase = str(edge.get("to") or "").strip()
        on_value = str(edge.get("on") or "").strip()

        if from_phase not in phase_ids:
            errors.append(f"control_flow[{index}]:invalid_from:{from_phase}")
        else:
            linked.add(from_phase)

        if to_phase == "end":
            has_terminal = True
        elif to_phase not in phase_ids:
            errors.append(f"control_flow[{index}]:invalid_to:{to_phase}")
        else:
            linked.add(to_phase)

        if on_value not in CONTROL_EDGE_ON:
            errors.append(f"control_flow[{index}]:invalid_on:{on_value}")

    if not has_terminal:
        errors.append("control_flow:no_terminal_end")

    for phase_id in sorted(phase_ids):
        if phase_id not in linked:
            errors.append(f"phase_closure_violation:unlinked_phase:{phase_id}")

    return errors


def validate_fail_policy(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    fail_policy = data.get("fail_policy")
    if not isinstance(fail_policy, dict):
        return ["invalid_fail_policy"]

    mode = str(fail_policy.get("mode") or "").strip()
    if mode != "fail_closed":
        errors.append("fail_policy:mode_must_be_fail_closed")

    retry = fail_policy.get("retry")
    if not isinstance(retry, dict):
        errors.append("fail_policy:retry_required")
    else:
        has_max = isinstance(retry.get("max_iterations"), int) or isinstance(retry.get("max_attempts"), int)
        if not has_max:
            errors.append("fail_policy:retry_missing_max_iterations_or_max_attempts")

    escalation_chain = fail_policy.get("escalation_chain")
    if not isinstance(escalation_chain, list) or not escalation_chain:
        errors.append("fail_policy:escalation_chain_required")

    return errors


def validate_lineage_policy(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    lineage_policy = data.get("lineage_policy")
    if not isinstance(lineage_policy, dict):
        return ["invalid_lineage_policy"]

    if not isinstance(lineage_policy.get("stack_depth_limit"), int):
        errors.append("lineage_policy:stack_depth_limit_required")
    if not str(lineage_policy.get("context_isolation") or "").strip():
        errors.append("lineage_policy:context_isolation_required")
    if not str(lineage_policy.get("output_handoff_mode") or "").strip():
        errors.append("lineage_policy:output_handoff_mode_required")
    return errors


def validate_collaboration_policy(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    process_level = str(data.get("process_level") or "").strip().lower()
    phases = data.get("phases")
    actors: Set[str] = set()
    if isinstance(phases, list):
        for phase in phases:
            if not isinstance(phase, dict):
                continue
            actor = str(phase.get("actor") or "").strip()
            if actor:
                actors.add(actor)

    strong_collaboration = len(actors) > 1
    require_policy = process_level == "p4" or (process_level in {"p5", "p6"} and strong_collaboration)
    policy = data.get("collaboration_policy")

    if require_policy and not isinstance(policy, dict):
        if process_level == "p4":
            errors.append("collaboration_policy:required_for_p4")
        else:
            errors.append("collaboration_policy:required_for_multi_actor_p5_p6")
        return errors

    if policy is None:
        return errors

    if not isinstance(policy, dict):
        errors.append("collaboration_policy:must_be_object")
        return errors

    for field in COLLABORATION_POLICY_REQUIRED_FIELDS:
        if not str(policy.get(field) or "").strip():
            errors.append(f"collaboration_policy:missing_{field}")

    return errors


def validate_evidence_policy(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    evidence_policy = data.get("evidence_policy")
    if not isinstance(evidence_policy, dict):
        return ["invalid_evidence_policy"]

    required_fields = evidence_policy.get("required_fields")
    if not isinstance(required_fields, list) or not required_fields:
        errors.append("evidence_policy:required_fields_required")
        return errors

    required_minimum = {"timestamp", "phase_id", "actor", "input_ref", "output_ref", "decision", "reason"}
    if not required_minimum.issubset(set(required_fields)):
        missing = sorted(required_minimum.difference(set(required_fields)))
        errors.append(f"evidence_policy:missing_minimum_fields:{','.join(missing)}")
    return errors


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
        root = repo_root()
        process_ids, skill_ids = load_registry_ids(root)

        errors: List[str] = []
        errors.extend(validate_top_level(data))
        phase_errors, phase_ids = validate_phases(data=data, process_ids=process_ids, skill_ids=skill_ids)
        errors.extend(phase_errors)
        errors.extend(validate_control_flow(data, phase_ids))
        errors.extend(validate_fail_policy(data))
        errors.extend(validate_lineage_policy(data))
        errors.extend(validate_collaboration_policy(data))
        errors.extend(validate_evidence_policy(data))

        if errors:
            return fail_closed(
                output_path=output_path,
                report_path=report_path,
                reason_code="process_schema_violation",
                message="流程定义未通过 canonical 校验，已 fail-closed。",
                details={"errors": errors},
            )

        process_id = str(data["process_id"]).strip()
        version = str(data["version"]).strip()
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
                "version": version,
            },
            "validation_summary": {
                "phase_count": len(data.get("phases", [])),
                "control_edge_count": len(data.get("control_flow", [])),
                "inline_ap_used": any(isinstance(p, dict) and "inline_ap" in p for p in data.get("phases", [])),
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
                    "checked_fields": REQUIRED_TOP_LEVEL_FIELDS,
                    "phase_count": len(data.get("phases", [])),
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
