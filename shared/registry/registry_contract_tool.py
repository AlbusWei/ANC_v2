#!/usr/bin/env python3
"""Registry contract validator and projection tool.

Commands:
  - validate: strict contract validation for registry files.
  - generate-docs: render human-readable schema docs from entry_contract.
  - project-openclaw: project registry data to managed OpenClaw config paths.
  - check-protocol-consistency: enforce BPM/context/process protocol canonical contract.
  - verify: run validate + capability check + protocol check + docs check + projection check.
  - verify-m2: run M2 runtime hardening gate checks for one round directory.
  - verify-m6: run M6 runtime evidence and gate checks for one round directory.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import yaml
except Exception:  # pragma: no cover - dependency check
    yaml = None


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_DIR = ROOT / "shared" / "registry"
CONFIG_DIR = ROOT / "config"
DOC_PATH = ROOT / "docs" / "design" / "data-models" / "registry-schemas.md"
PROFILE_PATH = CONFIG_DIR / "openclaw.projection.profiles.json"
SKILLS_DIR = ROOT / "skills"
PROCESS_ARCH_PATH = ROOT / "docs" / "architecture" / "process_architecture.md"
BPM_PROTOCOL_PATH = ROOT / "docs" / "design" / "interfaces" / "bpm-actor-protocol.md"
CONTEXT_SCHEMAS_PATH = ROOT / "docs" / "design" / "data-models" / "context-schemas.md"
PROCESS_SCHEMAS_PATH = ROOT / "docs" / "design" / "data-models" / "process-instance-schemas.md"
ROLE_HANDOFF_PATH = ROOT / "docs" / "design" / "interfaces" / "role-handoff-protocol.md"
OPENSPEC_PROTOCOL_PATH = ROOT / "docs" / "design" / "interfaces" / "openspec-collaboration-protocol.md"
OPENSPEC_SCHEMA_PATH = ROOT / "docs" / "design" / "data-models" / "openspec-collaboration-schema.json"
CONSTRUCTION_PLANE_PATH = ROOT / "docs" / "architecture" / "construction_plane.md"
M2_PROCESS_INVENTORY_PATH = ROOT / "docs" / "design" / "inventories" / "process-inventory.md"
M2_SKILL_INVENTORY_PATH = ROOT / "docs" / "design" / "inventories" / "skill-inventory.md"
M2_AGENT_INVENTORY_PATH = ROOT / "docs" / "design" / "inventories" / "agent-inventory.md"
M6_MANIFEST_PATH = ROOT / "processes" / "meta" / "construction-plane-governance" / "process.json"
PROCESS_MANIFESTS = [
    ROOT / "processes" / "meta" / "development-process" / "process.json",
    ROOT / "processes" / "meta" / "full-development" / "process.json",
    ROOT / "processes" / "meta" / "hotfix" / "process.json",
    ROOT / "processes" / "meta" / "refactor" / "process.json",
    ROOT / "processes" / "meta" / "governed-config-change" / "process.json",
    ROOT / "processes" / "meta" / "runtime-policy-calibration" / "process.json",
    ROOT / "processes" / "meta" / "construction-plane-governance" / "process.json",
    ROOT / "processes" / "control" / "trigger-schedule-runtime" / "process.json",
    ROOT / "processes" / "control" / "trigger-event-runtime" / "process.json",
]

AGENT_REGISTRY = REGISTRY_DIR / "agent_directory.json"
SKILL_REGISTRY = REGISTRY_DIR / "skill_registry.json"
PROCESS_REGISTRY = REGISTRY_DIR / "process_registry.json"
REGISTRY_FILES = [AGENT_REGISTRY, SKILL_REGISTRY, PROCESS_REGISTRY]

CAPABILITY_HEADING = "## Capability Contract (Machine-Readable)"
CAPABILITY_BLOCK_RE = re.compile(
    r"^## Capability Contract \(Machine-Readable\)\s*\n```yaml\s*\n(?P<body>.*?)\n```",
    re.MULTILINE | re.DOTALL,
)
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
REPO_REL_PATH_RE = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$)).+")
PROTOCOL_BLOCK_RE = re.compile(
    r"^### BPM Protocol Canonical Schema \(Machine-Readable\)\s*\n```yaml\s*\n(?P<body>.*?)\n```",
    re.MULTILINE | re.DOTALL,
)
JSON_BLOCK_RE = re.compile(
    r"```json\s*\n(?P<body>.*?)\n```",
    re.MULTILINE | re.DOTALL,
)
ROUND_ID_RE = re.compile(r"^R-\d{8}-M6-[a-z0-9-]+-\d{2}$")


class ContractError(Exception):
    pass


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def write_if_changed(path: Path, content: str, check: bool) -> bool:
    previous = ""
    if path.exists():
        previous = path.read_text(encoding="utf-8")
    changed = previous != content
    if check:
        return changed
    if changed:
        path.write_text(content, encoding="utf-8")
    return changed


def _type_ok(value: Any, type_name: str) -> bool:
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "null":
        return value is None
    return False


def _unique_items(seq: Sequence[Any]) -> bool:
    seen = set()
    for item in seq:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key in seen:
            return False
        seen.add(key)
    return True


def validate_by_schema(value: Any, schema: Dict[str, Any], path: str, errors: List[str]) -> None:
    expected_type = schema.get("type")
    if expected_type is not None:
        if isinstance(expected_type, list):
            ok = any(_type_ok(value, t) for t in expected_type)
        else:
            ok = _type_ok(value, expected_type)
        if not ok:
            errors.append(f"{path}: expected type {expected_type}, got {type(value).__name__}")
            return

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} not in enum {schema['enum']!r}")

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: value {value!r} must equal const {schema['const']!r}")

    if isinstance(value, str) and "pattern" in schema:
        pattern = schema["pattern"]
        if re.match(pattern, value) is None:
            errors.append(f"{path}: value {value!r} does not match pattern {pattern!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: value {value} < minimum {schema['minimum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: item count {len(value)} < minItems {schema['minItems']}")
        if schema.get("uniqueItems") and not _unique_items(value):
            errors.append(f"{path}: array items are not unique")
        if "items" in schema:
            for idx, item in enumerate(value):
                validate_by_schema(item, schema["items"], f"{path}[{idx}]", errors)

    if isinstance(value, dict):
        required = set(schema.get("required", []))
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required key {key!r}")

        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)

        for key, subvalue in value.items():
            if key in properties:
                validate_by_schema(subvalue, properties[key], f"{path}.{key}", errors)
            elif additional is False:
                errors.append(f"{path}: unknown key {key!r} is not allowed")
            elif isinstance(additional, dict):
                validate_by_schema(subvalue, additional, f"{path}.{key}", errors)


def validate_registry_contract(registry_path: Path, payload: Dict[str, Any], errors: List[str]) -> None:
    required_top = ["schema_version", "registry", "updated_at", "entry_contract", "entries"]
    for key in required_top:
        if key not in payload:
            errors.append(f"{registry_path}: missing top-level key {key!r}")
    if errors:
        return

    entry_contract = payload["entry_contract"]
    if not isinstance(entry_contract, dict):
        errors.append(f"{registry_path}: entry_contract must be object")
        return

    if "properties" not in entry_contract:
        errors.append(f"{registry_path}: entry_contract.properties is required")
        return

    if "required" not in entry_contract:
        errors.append(f"{registry_path}: entry_contract.required is required")
        return

    if entry_contract.get("additionalProperties") is not False:
        errors.append(
            f"{registry_path}: entry_contract.additionalProperties must be false for strict fail-closed behavior"
        )

    entries = payload["entries"]
    if not isinstance(entries, list):
        errors.append(f"{registry_path}: entries must be an array")
        return

    for index, entry in enumerate(entries):
        validate_by_schema(entry, entry_contract, f"{registry_path.name}.entries[{index}]", errors)


def _resolve_repo_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return ROOT / path


def _is_repo_relative_path(path_str: str) -> bool:
    if re.match(REPO_REL_PATH_RE, path_str) is None:
        return False
    return True


def path_exists(path_str: str) -> bool:
    return _resolve_repo_path(path_str).exists()


def _skill_relative_key(path: Path) -> str:
    if path.is_absolute():
        try:
            return path.relative_to(SKILLS_DIR).as_posix()
        except ValueError:
            return path.as_posix()

    normalized = path.as_posix()
    if normalized.startswith("skills/"):
        return normalized.split("skills/", 1)[1]
    return normalized


def _expect_non_empty_string(value: Any, path: str, errors: List[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected non-empty string")


def _expect_string_list(value: Any, path: str, errors: List[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path}: expected non-empty list of strings")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{path}[{index}]: expected non-empty string")


def _expect_repo_path(value: Any, path: str, errors: List[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{path}: expected path string")
        return
    if not _is_repo_relative_path(value):
        errors.append(f"{path}: path {value!r} must be repo-relative and cannot use '..'")
        return
    if not path_exists(value):
        errors.append(f"{path}: missing path {value}")


def _validate_capability_contract(contract: Dict[str, Any], skill_path: Path, errors: List[str]) -> None:
    prefix = f"{skill_path}: capability_contract"
    required_keys = [
        "contract_version",
        "objective_ref",
        "input_contract",
        "output_contract",
        "fail_closed_rules",
        "test_mount",
    ]

    for key in required_keys:
        if key not in contract:
            errors.append(f"{prefix}: missing required key {key!r}")

    version = contract.get("contract_version")
    if not isinstance(version, str) or re.match(SEMVER_RE, version) is None:
        errors.append(f"{prefix}.contract_version: expected semver (x.y.z)")

    _expect_non_empty_string(contract.get("objective_ref"), f"{prefix}.objective_ref", errors)

    input_contract = contract.get("input_contract")
    if not isinstance(input_contract, dict):
        errors.append(f"{prefix}.input_contract: expected object")
    else:
        _expect_non_empty_string(input_contract.get("format"), f"{prefix}.input_contract.format", errors)
        _expect_string_list(input_contract.get("required"), f"{prefix}.input_contract.required", errors)
        _expect_string_list(input_contract.get("validation"), f"{prefix}.input_contract.validation", errors)

    output_contract = contract.get("output_contract")
    if not isinstance(output_contract, dict):
        errors.append(f"{prefix}.output_contract: expected object")
    else:
        _expect_non_empty_string(output_contract.get("format"), f"{prefix}.output_contract.format", errors)
        _expect_string_list(output_contract.get("required"), f"{prefix}.output_contract.required", errors)
        _expect_string_list(
            output_contract.get("machine_judgement"),
            f"{prefix}.output_contract.machine_judgement",
            errors,
        )

    _expect_string_list(contract.get("fail_closed_rules"), f"{prefix}.fail_closed_rules", errors)

    test_mount = contract.get("test_mount")
    if not isinstance(test_mount, dict):
        errors.append(f"{prefix}.test_mount: expected object")
    else:
        _expect_repo_path(test_mount.get("test_doc"), f"{prefix}.test_mount.test_doc", errors)
        _expect_repo_path(
            test_mount.get("methodology_ref"),
            f"{prefix}.test_mount.methodology_ref",
            errors,
        )

    references = contract.get("references")
    if references is None:
        return
    if not isinstance(references, dict):
        errors.append(f"{prefix}.references: expected object when present")
        return
    for key, value in references.items():
        _expect_repo_path(value, f"{prefix}.references.{key}", errors)


def _load_capability_contract(skill_path: Path, errors: List[str]) -> Optional[Dict[str, Any]]:
    content = skill_path.read_text(encoding="utf-8")
    matches = list(CAPABILITY_BLOCK_RE.finditer(content))
    if not matches:
        errors.append(f"{skill_path}: missing '{CAPABILITY_HEADING}' yaml block")
        return None
    if len(matches) > 1:
        errors.append(f"{skill_path}: multiple '{CAPABILITY_HEADING}' blocks found")
        return None
    if yaml is None:
        errors.append(f"{skill_path}: PyYAML is required to parse capability contract")
        return None

    body = matches[0].group("body")
    try:
        payload = yaml.safe_load(body)
    except Exception as exc:
        errors.append(f"{skill_path}: capability contract yaml parse error: {exc}")
        return None

    if not isinstance(payload, dict):
        errors.append(f"{skill_path}: capability contract must be a yaml object")
        return None

    _validate_capability_contract(payload, skill_path, errors)
    return payload


def validate_skill_capabilities(skill_entries: List[Dict[str, Any]], errors: List[str]) -> None:
    skill_files = sorted(SKILLS_DIR.rglob("SKILL.md"))
    if not skill_files:
        errors.append(f"{SKILLS_DIR}: no SKILL.md found")
        return

    capabilities_by_relpath: Dict[str, Dict[str, Any]] = {}
    for skill_path in skill_files:
        rel_key = _skill_relative_key(skill_path)
        contract = _load_capability_contract(skill_path, errors)
        if contract is None:
            continue
        capabilities_by_relpath[rel_key] = contract

    for entry in skill_entries:
        rel_key = _skill_relative_key(Path(entry["path"]))
        capability = capabilities_by_relpath.get(rel_key)
        if capability is None:
            errors.append(
                f"skill_registry: {entry['skill_id']} missing capability contract at {entry['path']}"
            )
            continue

        test_mount = capability.get("test_mount", {})
        expected_test_doc = entry["tests"]["test_doc"]
        expected_methodology = entry["tests"]["methodology_ref"]
        if test_mount.get("test_doc") != expected_test_doc:
            errors.append(
                f"skill_registry: {entry['skill_id']} test_doc mismatch "
                f"({test_mount.get('test_doc')!r} != {expected_test_doc!r})"
            )
        if test_mount.get("methodology_ref") != expected_methodology:
            errors.append(
                f"skill_registry: {entry['skill_id']} methodology_ref mismatch "
                f"({test_mount.get('methodology_ref')!r} != {expected_methodology!r})"
            )


def _status_projectable_for_agent(status: str) -> bool:
    return status in {"draft", "review", "active"}


def _status_projectable_for_skill_or_process(status: str, allow_draft: bool) -> bool:
    if status in {"review", "active"}:
        return True
    if status == "draft":
        return allow_draft
    return False


def cross_validate_registries(
    agents_payload: Dict[str, Any],
    skills_payload: Dict[str, Any],
    processes_payload: Dict[str, Any],
    errors: List[str],
) -> None:
    agent_entries = agents_payload["entries"]
    skill_entries = skills_payload["entries"]
    process_entries = processes_payload["entries"]

    agent_ids = {entry["agent_id"] for entry in agent_entries}

    for entry in agent_entries:
        owner = entry["owner"]
        if owner != "human" and owner not in agent_ids:
            errors.append(f"agent_directory: owner {owner!r} not found in agent_directory")

        if not path_exists(entry["path"]):
            errors.append(f"agent_directory: missing path {entry['path']}")

    for entry in skill_entries:
        owner = entry["owner"]
        if owner not in agent_ids:
            errors.append(f"skill_registry: owner {owner!r} not found in agent_directory")

        for path_field in ["path"]:
            if not path_exists(entry[path_field]):
                errors.append(f"skill_registry: missing {path_field} {entry[path_field]}")

        tests = entry["tests"]
        for path_field in ["test_doc", "methodology_ref"]:
            if not path_exists(tests[path_field]):
                errors.append(f"skill_registry: missing tests.{path_field} {tests[path_field]}")

        agentskills = entry["agentskills"]
        if agentskills["name"] != entry["name"]:
            errors.append(
                "skill_registry: agentskills.name must equal entry name "
                f"({agentskills['name']!r} != {entry['name']!r})"
            )

        openclaw = entry["openclaw"]
        if openclaw["entry_key"] != entry["skill_id"]:
            errors.append(
                "skill_registry: openclaw.entry_key must equal skill_id "
                f"({openclaw['entry_key']!r} != {entry['skill_id']!r})"
            )

        if not path_exists(openclaw["source"]):
            errors.append(f"skill_registry: missing openclaw.source {openclaw['source']}")

        mode = openclaw["projection_mode"]
        if mode == "bundle":
            if not openclaw.get("bundle_key") or not openclaw.get("bundle_source"):
                errors.append(
                    f"skill_registry: bundle projection requires bundle_key and bundle_source for {entry['skill_id']}"
                )
            elif not path_exists(openclaw["bundle_source"]):
                errors.append(
                    f"skill_registry: missing openclaw.bundle_source {openclaw['bundle_source']}"
                )

    for entry in process_entries:
        owner = entry["owner"]
        if owner not in agent_ids:
            errors.append(f"process_registry: owner {owner!r} not found in agent_directory")

        for path_field in ["skill_path", "manifest_path"]:
            if not path_exists(entry[path_field]):
                errors.append(f"process_registry: missing {path_field} {entry[path_field]}")

        openclaw = entry["openclaw"]
        if openclaw["entry_key"] != entry["process_id"]:
            errors.append(
                "process_registry: openclaw.entry_key must equal process_id "
                f"({openclaw['entry_key']!r} != {entry['process_id']!r})"
            )

        if not path_exists(openclaw["source"]):
            errors.append(f"process_registry: missing openclaw.source {openclaw['source']}")

        mode = openclaw["projection_mode"]
        if mode == "bundle":
            if not openclaw.get("bundle_key") or not openclaw.get("bundle_source"):
                errors.append(
                    f"process_registry: bundle projection requires bundle_key and bundle_source for {entry['process_id']}"
                )
            elif not path_exists(openclaw["bundle_source"]):
                errors.append(
                    f"process_registry: missing openclaw.bundle_source {openclaw['bundle_source']}"
                )


def validate_all_registries() -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    payloads: Dict[Path, Dict[str, Any]] = {}
    errors: List[str] = []
    for path in REGISTRY_FILES:
        payload = load_json(path)
        payloads[path] = payload
        validate_registry_contract(path, payload, errors)

    if not errors:
        cross_validate_registries(
            payloads[AGENT_REGISTRY], payloads[SKILL_REGISTRY], payloads[PROCESS_REGISTRY], errors
        )
        validate_skill_capabilities(payloads[SKILL_REGISTRY]["entries"], errors)

    if errors:
        raise ContractError("\n".join(errors))

    return payloads[AGENT_REGISTRY], payloads[SKILL_REGISTRY], payloads[PROCESS_REGISTRY]


def _load_protocol_canonical_contract(errors: List[str]) -> Optional[Dict[str, Any]]:
    if not PROCESS_ARCH_PATH.exists():
        errors.append(f"{PROCESS_ARCH_PATH}: missing file")
        return None
    content = PROCESS_ARCH_PATH.read_text(encoding="utf-8")
    match = PROTOCOL_BLOCK_RE.search(content)
    if not match:
        errors.append(
            f"{PROCESS_ARCH_PATH}: missing canonical yaml block under "
            "'### BPM Protocol Canonical Schema (Machine-Readable)'"
        )
        return None
    if yaml is None:
        errors.append(f"{PROCESS_ARCH_PATH}: PyYAML is required to parse canonical schema block")
        return None

    try:
        payload = yaml.safe_load(match.group("body"))
    except Exception as exc:
        errors.append(f"{PROCESS_ARCH_PATH}: canonical schema yaml parse error: {exc}")
        return None

    if not isinstance(payload, dict):
        errors.append(f"{PROCESS_ARCH_PATH}: canonical schema payload must be yaml object")
        return None

    for required in ["task_dispatch", "task_completion", "lineage"]:
        if required not in payload:
            errors.append(f"{PROCESS_ARCH_PATH}: canonical schema missing key {required!r}")
    return payload


def _extract_json_blocks(path: Path, errors: List[str]) -> List[Dict[str, Any]]:
    if not path.exists():
        errors.append(f"{path}: missing file")
        return []
    content = path.read_text(encoding="utf-8")
    blocks: List[Dict[str, Any]] = []
    for match in JSON_BLOCK_RE.finditer(content):
        body = match.group("body")
        try:
            parsed = json.loads(body)
        except Exception as exc:
            errors.append(f"{path}: json code block parse error: {exc}")
            continue
        if isinstance(parsed, dict):
            blocks.append(parsed)
    if not blocks:
        errors.append(f"{path}: no parseable json code block found")
    return blocks


def _assert_required_fields(payload: Dict[str, Any], required: Sequence[str], path: str, errors: List[str]) -> None:
    for field in required:
        if field not in payload:
            errors.append(f"{path}: missing required field {field!r}")


def _assert_no_legacy_aliases(content: str, path: Path, errors: List[str]) -> None:
    aliases = [
        r'"skill"\s*:',
        r'"skill_or_process"\s*:',
        r'"skill_or_subprocess"\s*:',
    ]
    for alias in aliases:
        if re.search(alias, content):
            errors.append(f"{path}: legacy alias detected ({alias})")


def _is_relative_anchor(value: str) -> bool:
    if not isinstance(value, str) or "#" not in value:
        return False
    ref_path, anchor = value.split("#", 1)
    if not ref_path or not anchor:
        return False
    return _is_repo_relative_path(ref_path)


def _validate_inline_ap_phase(
    *,
    phase: Dict[str, Any],
    prefix: str,
    target_id: Any,
    skill_ids: set[str],
    errors: List[str],
) -> None:
    inline_ap = phase.get("inline_ap")
    if not isinstance(inline_ap, dict):
        errors.append(f"{prefix}: subprocess target not found in process_registry requires inline_ap object")
        return

    for field in ["ap_id", "skill_id", "actor", "pierce_allowed"]:
        if field not in inline_ap:
            errors.append(f"{prefix}: inline_ap missing required field {field!r}")

    ap_id = inline_ap.get("ap_id")
    if not isinstance(ap_id, str) or not ap_id.strip():
        errors.append(f"{prefix}: inline_ap.ap_id must be non-empty string")
    elif ap_id != target_id:
        errors.append(f"{prefix}: inline_ap.ap_id must equal target_id")

    skill_id = inline_ap.get("skill_id")
    if not isinstance(skill_id, str) or not skill_id.strip():
        errors.append(f"{prefix}: inline_ap.skill_id must be non-empty string")
    elif skill_id not in skill_ids:
        errors.append(f"{prefix}: inline_ap.skill_id {skill_id!r} not found in skill_registry.skill_id")

    ap_actor = inline_ap.get("actor")
    if not isinstance(ap_actor, str) or not ap_actor.strip():
        errors.append(f"{prefix}: inline_ap.actor must be non-empty string")

    pierce_allowed = inline_ap.get("pierce_allowed")
    if not isinstance(pierce_allowed, bool):
        errors.append(f"{prefix}: inline_ap.pierce_allowed must be boolean")
    elif pierce_allowed and ap_actor != phase.get("actor"):
        errors.append(
            f"{prefix}: inline_ap.pierce_allowed=true requires inline_ap.actor equals phase.actor"
        )


def check_protocol_consistency(
    skills_payload: Dict[str, Any],
    processes_payload: Dict[str, Any],
) -> None:
    errors: List[str] = []
    canonical = _load_protocol_canonical_contract(errors)
    if canonical is None:
        raise ContractError("\n".join(errors))

    dispatch_required = canonical.get("task_dispatch", {}).get("required", [])
    completion_required = canonical.get("task_completion", {}).get("required", [])
    self_check_required = canonical.get("task_completion", {}).get("self_check_required", [])
    lineage_required = canonical.get("lineage", {}).get("recursive_requires", [])

    if not isinstance(dispatch_required, list) or not isinstance(completion_required, list):
        errors.append(f"{PROCESS_ARCH_PATH}: canonical schema required fields must be arrays")

    bpm_blocks = _extract_json_blocks(BPM_PROTOCOL_PATH, errors)
    context_blocks = _extract_json_blocks(CONTEXT_SCHEMAS_PATH, errors)
    process_blocks = _extract_json_blocks(PROCESS_SCHEMAS_PATH, errors)

    dispatch_block = next((b for b in bpm_blocks if b.get("type") == "task_dispatch"), None)
    completion_block = next((b for b in bpm_blocks if b.get("type") == "task_completion"), None)
    if dispatch_block is None:
        errors.append(f"{BPM_PROTOCOL_PATH}: missing task_dispatch block")
    else:
        _assert_required_fields(
            dispatch_block,
            dispatch_required,
            f"{BPM_PROTOCOL_PATH}:task_dispatch",
            errors,
        )
    if completion_block is None:
        errors.append(f"{BPM_PROTOCOL_PATH}: missing task_completion block")
    else:
        _assert_required_fields(
            completion_block,
            completion_required,
            f"{BPM_PROTOCOL_PATH}:task_completion",
            errors,
        )
        self_check = completion_block.get("self_check")
        if not isinstance(self_check, dict):
            errors.append(f"{BPM_PROTOCOL_PATH}:task_completion.self_check must be object")
        else:
            _assert_required_fields(
                self_check,
                self_check_required,
                f"{BPM_PROTOCOL_PATH}:task_completion.self_check",
                errors,
            )
            refs = self_check.get("rule_refs", [])
            if not isinstance(refs, list) or not refs:
                errors.append(f"{BPM_PROTOCOL_PATH}:task_completion.self_check.rule_refs must be non-empty array")
            else:
                for idx, ref in enumerate(refs):
                    if not isinstance(ref, str) or not _is_relative_anchor(ref):
                        errors.append(
                            f"{BPM_PROTOCOL_PATH}:task_completion.self_check.rule_refs[{idx}] "
                            "must be repo_relative_path#anchor"
                        )
        if "evidence" in completion_block:
            errors.append(f"{BPM_PROTOCOL_PATH}: legacy field 'evidence' is forbidden")

    phase_handoff = next((b for b in context_blocks if "process_lineage" in b), None)
    context_dispatch = next((b for b in context_blocks if "target_type" in b and "target_id" in b), None)
    context_completion = next((b for b in context_blocks if "self_check" in b), None)
    if phase_handoff is None:
        errors.append(f"{CONTEXT_SCHEMAS_PATH}: missing phase handoff block with process_lineage")
    else:
        lineage = phase_handoff.get("process_lineage")
        if not isinstance(lineage, dict):
            errors.append(f"{CONTEXT_SCHEMAS_PATH}: process_lineage must be object")
        else:
            _assert_required_fields(
                lineage,
                lineage_required,
                f"{CONTEXT_SCHEMAS_PATH}:process_lineage",
                errors,
            )
    if context_dispatch is None:
        errors.append(f"{CONTEXT_SCHEMAS_PATH}: missing task dispatch block")
    else:
        _assert_required_fields(
            context_dispatch,
            dispatch_required,
            f"{CONTEXT_SCHEMAS_PATH}:task_dispatch",
            errors,
        )
    if context_completion is None:
        errors.append(f"{CONTEXT_SCHEMAS_PATH}: missing task completion block")
    else:
        _assert_required_fields(
            context_completion,
            completion_required,
            f"{CONTEXT_SCHEMAS_PATH}:task_completion",
            errors,
        )

    for path in [BPM_PROTOCOL_PATH, CONTEXT_SCHEMAS_PATH, PROCESS_SCHEMAS_PATH]:
        _assert_no_legacy_aliases(path.read_text(encoding="utf-8"), path, errors)

    required_handoff = [
        "instance_id",
        "lineage_ref",
        "stack_depth",
        "phase_id",
        "objective_ref",
        "input_ref",
        "output_ref",
        "output_contract",
        "from_role",
        "to_role",
        "deadline",
        "risk_notes",
        "evidence_ref",
    ]
    role_handoff_text = ROLE_HANDOFF_PATH.read_text(encoding="utf-8") if ROLE_HANDOFF_PATH.exists() else ""
    if not role_handoff_text:
        errors.append(f"{ROLE_HANDOFF_PATH}: missing file or empty content")
    for field in required_handoff:
        if f"`{field}`" not in role_handoff_text:
            errors.append(f"{ROLE_HANDOFF_PATH}: missing required handoff field `{field}`")

    if process_blocks:
        process_schema = process_blocks[0]
        if "fail_policy" not in process_schema:
            errors.append(f"{PROCESS_SCHEMAS_PATH}: process schema must include fail_policy")
        if "control_flow" not in process_schema:
            errors.append(f"{PROCESS_SCHEMAS_PATH}: process schema must include control_flow")
        if "control" in process_schema:
            errors.append(f"{PROCESS_SCHEMAS_PATH}: legacy top-level field 'control' is forbidden")
        if "failure_policy" in process_schema:
            errors.append(f"{PROCESS_SCHEMAS_PATH}: legacy top-level field 'failure_policy' is forbidden")
        phases = process_schema.get("phases", [])
        if not isinstance(phases, list) or not phases:
            errors.append(f"{PROCESS_SCHEMAS_PATH}: phases must be non-empty array")
        else:
            phase_schema = phases[0]
            for field in ["target_type", "target_id", "requires_spec"]:
                if field not in phase_schema:
                    errors.append(f"{PROCESS_SCHEMAS_PATH}: phase schema missing field {field!r}")

    skill_ids = {entry["skill_id"] for entry in skills_payload.get("entries", [])}
    process_ids = {entry["process_id"] for entry in processes_payload.get("entries", [])}
    for manifest_path in PROCESS_MANIFESTS:
        if not manifest_path.exists():
            errors.append(f"{manifest_path}: missing process manifest")
            continue
        payload = load_json(manifest_path)

        if "control" in payload:
            errors.append(f"{manifest_path}: legacy top-level field 'control' is forbidden")
        if "failure_policy" in payload:
            errors.append(f"{manifest_path}: legacy top-level field 'failure_policy' is forbidden")
        if "control_flow" not in payload:
            errors.append(f"{manifest_path}: missing required top-level field 'control_flow'")
        if "fail_policy" not in payload:
            errors.append(f"{manifest_path}: missing required top-level field 'fail_policy'")

        phases = payload.get("phases", [])
        if not isinstance(phases, list) or not phases:
            errors.append(f"{manifest_path}: phases must be non-empty array")
            continue

        for idx, phase in enumerate(phases):
            prefix = f"{manifest_path}:phases[{idx}]"
            for field in ["phase_id", "actor", "target_type", "target_id", "requires_spec"]:
                if field not in phase:
                    errors.append(f"{prefix}: missing required field {field!r}")
            for legacy in ["skill", "skill_or_process", "skill_or_subprocess"]:
                if legacy in phase:
                    errors.append(f"{prefix}: legacy field {legacy!r} is forbidden")

            target_type = phase.get("target_type")
            target_id = phase.get("target_id")
            if target_type == "subprocess":
                if target_id not in process_ids:
                    _validate_inline_ap_phase(
                        phase=phase,
                        prefix=prefix,
                        target_id=target_id,
                        skill_ids=skill_ids,
                        errors=errors,
                    )
                elif "inline_ap" in phase:
                    errors.append(
                        f"{prefix}: registered subprocess target must not declare inline_ap"
                    )
            else:
                errors.append(f"{prefix}: target_type must be 'subprocess'")

            requires_spec = phase.get("requires_spec")
            if not isinstance(requires_spec, bool):
                errors.append(f"{prefix}: requires_spec must be boolean")
            elif requires_spec:
                spec_ref = phase.get("spec_ref")
                if not isinstance(spec_ref, str) or not spec_ref.strip():
                    errors.append(f"{prefix}: spec_ref is required when requires_spec=true")
                elif not _is_relative_anchor(spec_ref):
                    errors.append(f"{prefix}: spec_ref must be repo_relative_path#anchor")

    if errors:
        raise ContractError("\n".join(errors))


def check_openspec_collaboration_consistency(
    skills_payload: Dict[str, Any],
    processes_payload: Dict[str, Any],
) -> None:
    errors: List[str] = []

    if not OPENSPEC_SCHEMA_PATH.exists():
        errors.append(f"{OPENSPEC_SCHEMA_PATH}: missing schema file")
    else:
        schema_payload = load_json(OPENSPEC_SCHEMA_PATH)
        if not isinstance(schema_payload, dict):
            errors.append(f"{OPENSPEC_SCHEMA_PATH}: schema root must be object")
        else:
            required_top = ["$schema", "$id", "type", "required", "properties", "additionalProperties"]
            for key in required_top:
                if key not in schema_payload:
                    errors.append(f"{OPENSPEC_SCHEMA_PATH}: missing top-level key {key!r}")

            if schema_payload.get("type") != "object":
                errors.append(f"{OPENSPEC_SCHEMA_PATH}: type must be 'object'")
            if schema_payload.get("additionalProperties") is not False:
                errors.append(f"{OPENSPEC_SCHEMA_PATH}: additionalProperties must be false")

            expected_required = {
                "record_id",
                "round_id",
                "round_goal",
                "module_scope",
                "owner",
                "openspec_ref",
                "anc_design_refs",
                "decision_snapshot_ref",
                "sync_status",
                "sync_timestamp",
                "sync_actor",
                "trigger_mode",
                "inspection_profile",
                "risk_level",
                "conflict_state",
                "checkpoint_count",
                "commit_count",
                "evidence_bundle",
                "sync_actions",
            }
            required_fields = set(schema_payload.get("required", []))
            if required_fields != expected_required:
                errors.append(
                    f"{OPENSPEC_SCHEMA_PATH}: required fields must exactly match complete schema set "
                    f"(expected {sorted(expected_required)!r}, got {sorted(required_fields)!r})"
                )

            props = schema_payload.get("properties", {})
            if not isinstance(props, dict):
                errors.append(f"{OPENSPEC_SCHEMA_PATH}: properties must be object")
            else:
                round_id_pattern = props.get("round_id", {}).get("pattern")
                if round_id_pattern != "^R-\\d{8}-M6-[a-z0-9-]+-\\d{2}$":
                    errors.append(
                        f"{OPENSPEC_SCHEMA_PATH}: round_id pattern must be "
                        "'^R-\\\\d{8}-M6-[a-z0-9-]+-\\\\d{2}$'"
                    )

                sync_status_enum = props.get("sync_status", {}).get("enum", [])
                if sync_status_enum != ["in_sync", "needs_sync", "conflict", "blocked"]:
                    errors.append(
                        f"{OPENSPEC_SCHEMA_PATH}: sync_status enum must be "
                        "['in_sync','needs_sync','conflict','blocked']"
                    )

                trigger_mode_enum = props.get("trigger_mode", {}).get("enum", [])
                if trigger_mode_enum != ["change_triggered", "analyst_inspection"]:
                    errors.append(
                        f"{OPENSPEC_SCHEMA_PATH}: trigger_mode enum must be "
                        "['change_triggered','analyst_inspection']"
                    )

                conflict_required = props.get("conflict_state", {}).get("required", [])
                if set(conflict_required) != {"has_conflict", "resolved", "resolution_ref"}:
                    errors.append(
                        f"{OPENSPEC_SCHEMA_PATH}: conflict_state.required must include "
                        "'has_conflict', 'resolved', 'resolution_ref'"
                    )

                evidence_required = props.get("evidence_bundle", {}).get("required", [])
                if set(evidence_required) != {
                    "openspec_linkage_ref",
                    "anc_delta_index_ref",
                    "sync_check_report_ref",
                    "status_report_ref",
                    "round_evidence_log_ref",
                }:
                    errors.append(
                        f"{OPENSPEC_SCHEMA_PATH}: evidence_bundle.required must include all evidence refs"
                    )

    if not OPENSPEC_PROTOCOL_PATH.exists():
        errors.append(f"{OPENSPEC_PROTOCOL_PATH}: missing protocol document")
    else:
        protocol_text = OPENSPEC_PROTOCOL_PATH.read_text(encoding="utf-8")
        if "docs/design/data-models/openspec-collaboration-schema.json" not in protocol_text:
            errors.append(f"{OPENSPEC_PROTOCOL_PATH}: must reference OpenSpec collaboration schema path")

    skill_ids = {entry["skill_id"] for entry in skills_payload.get("entries", [])}
    for required_skill in ["sys.arch.construction-audit", "system.integration.openspec-sync"]:
        if required_skill not in skill_ids:
            errors.append(f"skill_registry: missing required OpenSpec governance skill {required_skill!r}")

    process_entries = {entry["process_id"]: entry for entry in processes_payload.get("entries", [])}
    m6_entry = process_entries.get("construction-plane-governance")
    if m6_entry is None:
        errors.append("process_registry: missing required process 'construction-plane-governance'")
    else:
        if m6_entry.get("owner") != "architect":
            errors.append("process_registry: construction-plane-governance owner must be 'architect'")
        if m6_entry.get("phase_count", 0) < 5:
            errors.append("process_registry: construction-plane-governance phase_count must be >= 5")

    if not M6_MANIFEST_PATH.exists():
        errors.append(f"{M6_MANIFEST_PATH}: missing process manifest")
    else:
        m6_manifest = load_json(M6_MANIFEST_PATH)
        input_required = set(m6_manifest.get("input_contract", {}).get("required", []))
        output_required = set(m6_manifest.get("output_contract", {}).get("required", []))
        if "round_id" not in input_required:
            errors.append(f"{M6_MANIFEST_PATH}: input_contract.required must include 'round_id'")
        if "openspec_ref" not in input_required:
            errors.append(f"{M6_MANIFEST_PATH}: input_contract.required must include 'openspec_ref'")
        if "openspec_sync_ref" not in output_required:
            errors.append(f"{M6_MANIFEST_PATH}: output_contract.required must include 'openspec_sync_ref'")
        if "round_evidence_log_ref" not in output_required:
            errors.append(f"{M6_MANIFEST_PATH}: output_contract.required must include 'round_evidence_log_ref'")
        if "round_close_summary_ref" not in output_required:
            errors.append(f"{M6_MANIFEST_PATH}: output_contract.required must include 'round_close_summary_ref'")

        phases = m6_manifest.get("phases", [])
        has_openspec_phase = False
        for phase in phases:
            if not isinstance(phase, dict):
                continue
            inline_ap = phase.get("inline_ap")
            inline_skill_id = inline_ap.get("skill_id") if isinstance(inline_ap, dict) else None
            if inline_skill_id == "system.integration.openspec-sync":
                has_openspec_phase = True
                break
        if not has_openspec_phase:
            errors.append(
                f"{M6_MANIFEST_PATH}: phases must include a phase using inline_ap.skill_id "
                "'system.integration.openspec-sync'"
            )

    if errors:
        raise ContractError("\n".join(errors))


def _load_jsonl_events(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise ContractError(f"{path}: missing round evidence log")

    events: List[Dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractError(f"{path}: invalid JSONL line {line_no}: {exc}") from exc
        if not isinstance(item, dict):
            raise ContractError(f"{path}: line {line_no} must be JSON object")
        events.append(item)
    return events


def _resolve_artifact_path(round_dir: Path, ref: str) -> Path:
    ref_path = Path(ref)
    if ref_path.is_absolute():
        return ref_path
    root_candidate = ROOT / ref_path
    if root_candidate.exists():
        return root_candidate
    return (round_dir / ref_path).resolve()


def _validate_m6_phase_ap_coverage(manifest: Dict[str, Any], errors: List[str]) -> None:
    phases = manifest.get("phases", [])
    if not isinstance(phases, list):
        errors.append(f"{M6_MANIFEST_PATH}: phases must be array")
        return
    expected = {"AP-032", "AP-033", "AP-034", "AP-035", "AP-036"}
    found: set[str] = set()
    for phase in phases:
        if not isinstance(phase, dict):
            continue
        spec_ref = phase.get("spec_ref")
        if isinstance(spec_ref, str):
            for ap in expected:
                if ap in spec_ref:
                    found.add(ap)
    missing = sorted(expected - found)
    if missing:
        errors.append(
            f"{M6_MANIFEST_PATH}: phases must cover AP-032~AP-036; missing {missing!r}"
        )


def _collect_git_commits(git_range: str, errors: List[str]) -> List[Tuple[str, str]]:
    proc = subprocess.run(
        ["git", "log", "--format=%H%n%B%n__END_COMMIT__", git_range],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        errors.append(f"git log failed for range {git_range!r}: {proc.stderr.strip()}")
        return []

    commits: List[Tuple[str, str]] = []
    for block in proc.stdout.split("__END_COMMIT__"):
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        sha = lines[0].strip()
        message = "\n".join(lines[1:]).strip()
        commits.append((sha, message))
    return commits


def _validate_round_evidence(
    events: List[Dict[str, Any]],
    git_range: Optional[str],
    errors: List[str],
) -> None:
    if not events:
        errors.append("round evidence log is empty")
        return

    allowed = {"round_open", "checkpoint_synced", "round_close"}
    event_names = [event.get("event") for event in events]
    for idx, event_name in enumerate(event_names):
        if event_name not in allowed:
            errors.append(f"round evidence event[{idx}] invalid event: {event_name!r}")

    if events[0].get("event") != "round_open":
        errors.append("round_open must be the first event")
    if events[-1].get("event") != "round_close":
        errors.append("round_close must be the last event")

    if event_names.count("round_open") != 1:
        errors.append("round_open must appear exactly once")
    if event_names.count("round_close") != 1:
        errors.append("round_close must appear exactly once")

    for idx, event in enumerate(events):
        round_id = event.get("round_id")
        openspec_ref = event.get("openspec_ref")
        if not isinstance(round_id, str) or re.match(ROUND_ID_RE, round_id) is None:
            errors.append(f"round evidence event[{idx}] invalid round_id: {round_id!r}")
        if not isinstance(openspec_ref, str) or not openspec_ref.strip():
            errors.append(f"round evidence event[{idx}] openspec_ref must be non-empty string")

    round_ids = {event.get("round_id") for event in events}
    openspec_refs = {event.get("openspec_ref") for event in events}
    if len(round_ids) != 1:
        errors.append(f"round evidence must contain single round_id, found {sorted(round_ids)!r}")
    if len(openspec_refs) != 1:
        errors.append(
            f"round evidence must contain single openspec_ref, found {sorted(openspec_refs)!r}"
        )

    checkpoint_events = [e for e in events if e.get("event") == "checkpoint_synced"]
    close_event = next((e for e in events if e.get("event") == "round_close"), None)
    if close_event:
        cp = close_event.get("checkpoint_count")
        cm = close_event.get("commit_count")
        if not isinstance(cp, int) or not isinstance(cm, int):
            errors.append("round_close checkpoint_count and commit_count must be integers")
        else:
            if cp != cm:
                errors.append("round_close checkpoint_count must equal commit_count")
            if cp != len(checkpoint_events):
                errors.append(
                    f"round_close checkpoint_count {cp} does not match checkpoint events {len(checkpoint_events)}"
                )

    if git_range:
        commits = _collect_git_commits(git_range, errors)
        for sha, message in commits:
            if re.search(r"^Entire-Checkpoint:\s+\S+", message, flags=re.MULTILINE) is None:
                errors.append(f"git commit missing Entire-Checkpoint trailer: {sha}")
        if close_event and isinstance(close_event.get("commit_count"), int):
            expected_count = close_event["commit_count"]
            if expected_count != len(commits):
                errors.append(
                    f"round_close commit_count {expected_count} does not match git range commits {len(commits)}"
                )


def _load_round_output(
    round_dir: Path,
    required_outputs: set[str],
    errors: List[str],
) -> Dict[str, Any]:
    round_output_path = round_dir / "round-output.json"
    if not round_output_path.exists():
        errors.append(f"{round_output_path}: missing round output bundle")
        return {}

    round_output = load_json(round_output_path)
    if not isinstance(round_output, dict):
        errors.append(f"{round_output_path}: must be JSON object")
        return {}

    missing = sorted(required_outputs - set(round_output.keys()))
    if missing:
        errors.append(f"{round_output_path}: missing required output fields {missing!r}")
    return round_output


def _check_round_output_ref(
    round_dir: Path,
    round_output: Dict[str, Any],
    ref_field: str,
    errors: List[str],
    *,
    gate_prefix: Optional[str] = None,
) -> None:
    ref_value = round_output.get(ref_field)
    label = f"{gate_prefix}: {ref_field}" if gate_prefix else ref_field
    if not isinstance(ref_value, str) or not ref_value.strip():
        errors.append(f"{label} missing")
        return
    ref_path = _resolve_artifact_path(round_dir, ref_value)
    if not ref_path.exists():
        errors.append(f"{label} missing file {ref_path}")


def _validate_m2_status_targets(
    agents_payload: Dict[str, Any],
    skills_payload: Dict[str, Any],
    processes_payload: Dict[str, Any],
    errors: List[str],
) -> None:
    agent_by_id = {entry["agent_id"]: entry for entry in agents_payload.get("entries", [])}
    skill_by_id = {entry["skill_id"]: entry for entry in skills_payload.get("entries", [])}
    process_by_id = {entry["process_id"]: entry for entry in processes_payload.get("entries", [])}

    targets = [
        ("agent_directory", "system-analyst", "review", agent_by_id),
        ("skill_registry", "sys.arch.system-feedback-digest", "review", skill_by_id),
        ("process_registry", "runtime-policy-calibration", "review", process_by_id),
    ]
    for registry_name, asset_id, expected_status, table in targets:
        entry = table.get(asset_id)
        if entry is None:
            errors.append(f"{registry_name}: missing required M2 asset {asset_id!r}")
            continue
        actual_status = entry.get("status")
        if actual_status != expected_status:
            errors.append(
                f"{registry_name}: {asset_id} status must be {expected_status!r}, got {actual_status!r}"
            )


def _validate_m2_doc_linkage(errors: List[str]) -> None:
    required_paths = [
        CONSTRUCTION_PLANE_PATH,
        M2_PROCESS_INVENTORY_PATH,
        M2_SKILL_INVENTORY_PATH,
        M2_AGENT_INVENTORY_PATH,
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"{path}: missing required M2 linkage document")
            return

    construction_text = CONSTRUCTION_PLANE_PATH.read_text(encoding="utf-8")
    if re.search(r"^\|\s*Q-001\s*\|.*\|\s*Closed", construction_text, flags=re.MULTILINE) is None:
        errors.append(f"{CONSTRUCTION_PLANE_PATH}: Q-001 must be marked Closed")
    if "Q-001 保持未关闭" in construction_text:
        errors.append(f"{CONSTRUCTION_PLANE_PATH}: stale unresolved Q-001 marker detected")

    process_text = M2_PROCESS_INVENTORY_PATH.read_text(encoding="utf-8")
    if (
        re.search(
            r"^\|\s*runtime-policy-calibration\s*\|.*\|\s*review\s*\|",
            process_text,
            flags=re.MULTILINE,
        )
        is None
    ):
        errors.append(
            f"{M2_PROCESS_INVENTORY_PATH}: runtime-policy-calibration inventory status must be review"
        )

    agent_text = M2_AGENT_INVENTORY_PATH.read_text(encoding="utf-8")
    if (
        re.search(
            r"^\|\s*system-analyst\s*\|.*\|\s*review\s*\|",
            agent_text,
            flags=re.MULTILINE,
        )
        is None
    ):
        errors.append(f"{M2_AGENT_INVENTORY_PATH}: system-analyst inventory status must be review")

    skill_text = M2_SKILL_INVENTORY_PATH.read_text(encoding="utf-8")
    if "生命周期状态为 `review`" not in skill_text:
        errors.append(
            f"{M2_SKILL_INVENTORY_PATH}: must record W5 lifecycle state as review for M2 close-out"
        )


def _run_verify_m2_cmd(args: argparse.Namespace) -> int:
    agents_payload, skills_payload, processes_payload = validate_all_registries()
    check_protocol_consistency(skills_payload, processes_payload)
    check_openspec_collaboration_consistency(skills_payload, processes_payload)

    errors: List[str] = []
    round_dir = Path(args.round_dir)
    if not round_dir.is_absolute():
        round_dir = (ROOT / round_dir).resolve()
    if not round_dir.exists() or not round_dir.is_dir():
        raise ContractError(f"round_dir not found: {round_dir}")

    required_outputs = {"round_evidence_log_ref", "round_close_summary_ref", "registry_verify_report_ref"}
    round_output = _load_round_output(round_dir, required_outputs, errors)
    _check_round_output_ref(
        round_dir,
        round_output,
        "round_close_summary_ref",
        errors,
        gate_prefix="pre-close gate",
    )
    _check_round_output_ref(round_dir, round_output, "registry_verify_report_ref", errors)

    round_evidence_ref = round_output.get("round_evidence_log_ref")
    if isinstance(round_evidence_ref, str) and round_evidence_ref.strip():
        evidence_path = _resolve_artifact_path(round_dir, round_evidence_ref)
    else:
        evidence_path = round_dir / "round-evidence.jsonl"
    events = _load_jsonl_events(evidence_path)
    _validate_round_evidence(events, git_range=args.git_range, errors=errors)

    _validate_m2_status_targets(agents_payload, skills_payload, processes_payload, errors)
    _validate_m2_doc_linkage(errors)

    if errors:
        raise ContractError("\n".join(errors))

    print(f"verify-m2 passed for {round_dir}")
    return 0


def _run_verify_m6_cmd(args: argparse.Namespace) -> int:
    _, skills_payload, processes_payload = validate_all_registries()
    check_protocol_consistency(skills_payload, processes_payload)
    check_openspec_collaboration_consistency(skills_payload, processes_payload)

    errors: List[str] = []
    round_dir = Path(args.round_dir)
    if not round_dir.is_absolute():
        round_dir = (ROOT / round_dir).resolve()
    if not round_dir.exists() or not round_dir.is_dir():
        raise ContractError(f"round_dir not found: {round_dir}")

    manifest_payload = load_json(M6_MANIFEST_PATH)
    _validate_m6_phase_ap_coverage(manifest_payload, errors)

    required_outputs = set(manifest_payload.get("output_contract", {}).get("required", []))
    round_output = _load_round_output(round_dir, required_outputs, errors)

    _check_round_output_ref(
        round_dir,
        round_output,
        "round_close_summary_ref",
        errors,
        gate_prefix="pre-close gate",
    )

    round_evidence_ref = round_output.get("round_evidence_log_ref")
    if isinstance(round_evidence_ref, str) and round_evidence_ref.strip():
        evidence_path = _resolve_artifact_path(round_dir, round_evidence_ref)
    else:
        evidence_path = round_dir / "round-evidence.jsonl"
    events = _load_jsonl_events(evidence_path)
    _validate_round_evidence(events, git_range=args.git_range, errors=errors)

    openspec_sync_ref = round_output.get("openspec_sync_ref")
    if not isinstance(openspec_sync_ref, str) or not openspec_sync_ref.strip():
        errors.append("round output missing openspec_sync_ref")
    else:
        openspec_path = _resolve_artifact_path(round_dir, openspec_sync_ref)
        if not openspec_path.exists():
            errors.append(f"openspec_sync_ref file missing: {openspec_path}")
        else:
            record = load_json(openspec_path)
            schema_payload = load_json(OPENSPEC_SCHEMA_PATH)
            schema_errors: List[str] = []
            validate_by_schema(record, schema_payload, "openspec_sync_record", schema_errors)
            if schema_errors:
                errors.extend(schema_errors)

    registry_verify_ref = round_output.get("registry_verify_report_ref")
    if not isinstance(registry_verify_ref, str) or not registry_verify_ref.strip():
        errors.append("round output missing registry_verify_report_ref")
    else:
        registry_verify_path = _resolve_artifact_path(round_dir, registry_verify_ref)
        if not registry_verify_path.exists():
            errors.append(f"registry_verify_report_ref file missing: {registry_verify_path}")

    if errors:
        raise ContractError("\n".join(errors))

    print(f"verify-m6 passed for {round_dir}")
    return 0


def _schema_type(schema: Dict[str, Any]) -> str:
    t = schema.get("type", "any")
    if isinstance(t, list):
        return "|".join(t)
    if t == "array":
        item_t = _schema_type(schema.get("items", {}))
        return f"array<{item_t}>"
    return str(t)


def _constraints(schema: Dict[str, Any]) -> str:
    parts: List[str] = []
    if "enum" in schema:
        parts.append("enum=" + ",".join(str(v) for v in schema["enum"]))
    if "pattern" in schema:
        parts.append("pattern=" + schema["pattern"])
    if "minimum" in schema:
        parts.append(f"min={schema['minimum']}")
    if "minItems" in schema:
        parts.append(f"minItems={schema['minItems']}")
    if schema.get("uniqueItems"):
        parts.append("uniqueItems=true")
    return "; ".join(parts)


def _flatten_properties(
    schema: Dict[str, Any],
    required: Iterable[str],
    prefix: str = "",
) -> List[Tuple[str, Dict[str, Any], bool]]:
    rows: List[Tuple[str, Dict[str, Any], bool]] = []
    props = schema.get("properties", {})
    req_set = set(required)
    for key, subschema in props.items():
        field = f"{prefix}.{key}" if prefix else key
        is_required = key in req_set
        rows.append((field, subschema, is_required))
        if subschema.get("type") == "object":
            nested_required = subschema.get("required", [])
            rows.extend(_flatten_properties(subschema, nested_required, prefix=field))
    return rows


def generate_docs(agents_payload: Dict[str, Any], skills_payload: Dict[str, Any], processes_payload: Dict[str, Any]) -> str:
    registries = [
        ("agent_directory.json", agents_payload),
        ("skill_registry.json", skills_payload),
        ("process_registry.json", processes_payload),
    ]

    lines: List[str] = []
    lines.append("# 注册表 Schema 详细定义")
    lines.append("")
    lines.append(
        "> 本文档由 `shared/registry/registry_contract_tool.py` 自动生成。"
    )
    lines.append("> 机器真相源：`shared/registry/*_registry.json` 中的 `entry_contract`。")
    lines.append("")

    for filename, payload in registries:
        contract = payload["entry_contract"]
        lines.append(f"## {filename}")
        lines.append("")
        lines.append(f"- schema_version: `{payload['schema_version']}`")
        lines.append(f"- updated_at: `{payload['updated_at']}`")
        lines.append(f"- strict mode: `{str(contract.get('additionalProperties') is False).lower()}`")
        lines.append("")
        lines.append("| 字段 | 类型 | 必填 | 约束 | 说明 |")
        lines.append("|---|---|---|---|---|")

        rows = _flatten_properties(contract, contract.get("required", []))
        for field, schema, required in rows:
            desc = schema.get("description", "")
            lines.append(
                f"| `{field}` | `{_schema_type(schema)}` | `{str(required).lower()}` | `{_constraints(schema)}` | {desc} |"
            )

        lines.append("")
        lines.append("示例条目：")
        lines.append("")
        lines.append("```json")
        example = payload["entries"][0] if payload["entries"] else {}
        lines.append(json.dumps(example, indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append("")

    lines.append("## 校验命令")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 shared/registry/registry_contract_tool.py validate")
    lines.append(
        "python3 shared/registry/registry_contract_tool.py generate-docs --check"
    )
    lines.append(
        "python3 shared/registry/registry_contract_tool.py project-openclaw --all --check"
    )
    lines.append(
        "python3 shared/registry/registry_contract_tool.py check-protocol-consistency"
    )
    lines.append("python3 shared/registry/registry_contract_tool.py verify")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def load_profiles() -> Dict[str, Any]:
    payload = load_json(PROFILE_PATH)
    required_top = ["version", "managed_paths", "profiles"]
    for key in required_top:
        if key not in payload:
            raise ContractError(f"{PROFILE_PATH}: missing key {key!r}")

    managed = payload["managed_paths"]
    if managed.get("agents_list") != "agents.list" or managed.get("skills_entries") != "skills.entries":
        raise ContractError(
            f"{PROFILE_PATH}: managed_paths must pin agents.list and skills.entries"
        )

    profiles = payload["profiles"]
    if not isinstance(profiles, dict) or not profiles:
        raise ContractError(f"{PROFILE_PATH}: profiles must be a non-empty object")

    for name, profile in profiles.items():
        for key in ["output_file", "include_agents", "allow_agent_status"]:
            if key not in profile:
                raise ContractError(f"{PROFILE_PATH}: profile {name!r} missing {key!r}")

    return payload


def _set_nested(container: Dict[str, Any], dotted_path: str, value: Any) -> None:
    parts = dotted_path.split(".")
    cur = container
    for part in parts[:-1]:
        if part not in cur or not isinstance(cur[part], dict):
            cur[part] = {}
        cur = cur[part]
    cur[parts[-1]] = value


def _extract_channel_names(config_payload: Dict[str, Any]) -> set[str]:
    channels = config_payload.get("channels")
    if channels is None:
        return set()
    if isinstance(channels, dict):
        return set(channels.keys())
    if isinstance(channels, list):
        out = set()
        for item in channels:
            if isinstance(item, str):
                out.add(item)
            elif isinstance(item, dict):
                name = item.get("name") or item.get("id")
                if isinstance(name, str):
                    out.add(name)
        return out
    return set()


def _build_agents_list(
    agent_entries: List[Dict[str, Any]],
    profile: Dict[str, Any],
    channel_names: set[str],
) -> List[Dict[str, str]]:
    by_id = {entry["agent_id"]: entry for entry in agent_entries}
    wanted = profile["include_agents"]
    allowed_status = set(profile["allow_agent_status"])

    result = []
    for agent_id in wanted:
        if agent_id not in by_id:
            raise ContractError(f"profile references unknown agent_id {agent_id!r}")
        entry = by_id[agent_id]
        if entry["status"] not in allowed_status:
            raise ContractError(
                f"agent {agent_id!r} has status {entry['status']!r} not allowed by profile"
            )

        for ch in entry["bindings"]["channels"]:
            if channel_names and ch not in channel_names:
                raise ContractError(
                    f"agent {agent_id!r} references unknown channel {ch!r} in bindings.channels"
                )

        result.append({"id": entry["agent_id"], "workspace": entry["path"]})
    return result


def _collect_projected_skill_entries(
    entries: List[Dict[str, Any]],
    kind: str,
) -> Tuple[Dict[str, str], Dict[str, str], List[str]]:
    bundles: Dict[str, str] = {}
    pins: Dict[str, str] = {}
    warnings: List[str] = []

    for entry in entries:
        status = entry["status"]
        openclaw = entry["openclaw"]
        mode = openclaw["projection_mode"]
        allow_draft = openclaw.get("allow_draft_projection", False)

        if mode == "off":
            continue

        if status in {"deprecated", "retired"}:
            warnings.append(
                f"skip {kind} {entry.get('skill_id') or entry.get('process_id')}: status={status}"
            )
            continue

        if not _status_projectable_for_skill_or_process(status, allow_draft):
            warnings.append(
                f"skip {kind} {entry.get('skill_id') or entry.get('process_id')}: "
                f"status={status} without allow_draft_projection"
            )
            continue

        if mode == "bundle":
            bundle_key = openclaw.get("bundle_key")
            bundle_source = openclaw.get("bundle_source")
            if not bundle_key or not bundle_source:
                raise ContractError(
                    f"{kind} {entry.get('skill_id') or entry.get('process_id')} missing bundle_key/bundle_source"
                )
            existing = bundles.get(bundle_key)
            if existing is not None and existing != bundle_source:
                raise ContractError(
                    f"bundle_key {bundle_key!r} has conflicting sources: {existing!r} vs {bundle_source!r}"
                )
            bundles[bundle_key] = bundle_source
        elif mode == "pin":
            pins[openclaw["entry_key"]] = openclaw["source"]
        else:
            raise ContractError(f"unsupported projection_mode {mode!r}")

    return bundles, pins, warnings


def _build_skills_entries(
    skill_entries: List[Dict[str, Any]],
    process_entries: List[Dict[str, Any]],
) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
    bundle_map: Dict[str, str] = {}
    pin_map: Dict[str, str] = {}
    warnings: List[str] = []

    for kind, entries in (("skill", skill_entries), ("process", process_entries)):
        bundles, pins, item_warnings = _collect_projected_skill_entries(entries, kind)
        warnings.extend(item_warnings)

        for key, source in bundles.items():
            existing = bundle_map.get(key)
            if existing is not None and existing != source:
                raise ContractError(
                    f"bundle key {key!r} conflicts between registries: {existing!r} vs {source!r}"
                )
            bundle_map[key] = source

        for key, source in pins.items():
            pin_map[key] = source

    out: Dict[str, Dict[str, str]] = {}
    for key in sorted(bundle_map.keys()):
        out[key] = {"source": bundle_map[key]}

    # Pin entries override bundle entries when keys collide.
    for key in sorted(pin_map.keys()):
        out[key] = {"source": pin_map[key]}

    return out, warnings


def project_openclaw_configs(
    agents_payload: Dict[str, Any],
    skills_payload: Dict[str, Any],
    processes_payload: Dict[str, Any],
    profile_name: Optional[str],
    run_all: bool,
    check: bool,
) -> Tuple[bool, List[str]]:
    profiles_payload = load_profiles()
    profiles = profiles_payload["profiles"]
    managed_paths = profiles_payload["managed_paths"]

    selected: List[Tuple[str, Dict[str, Any]]] = []
    if run_all or profile_name is None:
        selected = [(name, profiles[name]) for name in profiles.keys()]
    else:
        if profile_name not in profiles:
            raise ContractError(f"unknown profile {profile_name!r}")
        selected = [(profile_name, profiles[profile_name])]

    changed_any = False
    warning_lines: List[str] = []

    for name, profile in selected:
        output_path = Path(profile["output_file"])
        if not output_path.is_absolute():
            output_path = ROOT / output_path

        existing = {}
        if output_path.exists():
            existing = load_json(output_path)

        channel_names = _extract_channel_names(existing)

        agents_list = _build_agents_list(agents_payload["entries"], profile, channel_names)
        skills_entries, warnings = _build_skills_entries(
            skills_payload["entries"], processes_payload["entries"]
        )
        warning_lines.extend([f"[{name}] {w}" for w in warnings])

        projected = json.loads(json.dumps(existing))
        _set_nested(projected, managed_paths["agents_list"], agents_list)
        _set_nested(projected, managed_paths["skills_entries"], skills_entries)

        content = dump_json(projected)
        changed = write_if_changed(output_path, content, check=check)
        changed_any = changed_any or changed

    return changed_any, warning_lines


def _run_validate_cmd(_args: argparse.Namespace) -> int:
    validate_all_registries()
    print("Registry contracts validated.")
    return 0


def _run_generate_docs_cmd(args: argparse.Namespace) -> int:
    agents_payload, skills_payload, processes_payload = validate_all_registries()
    content = generate_docs(agents_payload, skills_payload, processes_payload)
    changed = write_if_changed(DOC_PATH, content, check=args.check)

    if args.check and changed:
        print(f"Generated docs are stale: {DOC_PATH}")
        return 1

    if not args.check:
        print(f"Generated docs: {DOC_PATH}")
    else:
        print("Registry schema docs are up to date.")
    return 0


def _run_project_cmd(args: argparse.Namespace) -> int:
    agents_payload, skills_payload, processes_payload = validate_all_registries()
    changed, warnings = project_openclaw_configs(
        agents_payload,
        skills_payload,
        processes_payload,
        profile_name=args.profile,
        run_all=args.all,
        check=args.check,
    )

    for warning in warnings:
        print(f"WARN: {warning}")

    if args.check and changed:
        print("Projected OpenClaw config is stale.")
        return 1

    if args.check:
        print("Projected OpenClaw config is up to date.")
    else:
        print("Projected OpenClaw config updated.")
    return 0


def _run_protocol_consistency_cmd(_args: argparse.Namespace) -> int:
    _, skills_payload, processes_payload = validate_all_registries()
    check_protocol_consistency(skills_payload, processes_payload)
    check_openspec_collaboration_consistency(skills_payload, processes_payload)
    print("Protocol consistency passed.")
    return 0


def _run_verify_cmd(_args: argparse.Namespace) -> int:
    agents_payload, skills_payload, processes_payload = validate_all_registries()
    check_protocol_consistency(skills_payload, processes_payload)
    check_openspec_collaboration_consistency(skills_payload, processes_payload)

    docs_content = generate_docs(agents_payload, skills_payload, processes_payload)
    docs_changed = write_if_changed(DOC_PATH, docs_content, check=True)

    projection_changed, warnings = project_openclaw_configs(
        agents_payload,
        skills_payload,
        processes_payload,
        profile_name=None,
        run_all=True,
        check=True,
    )

    for warning in warnings:
        print(f"WARN: {warning}")

    failed = False
    if docs_changed:
        print(f"Stale generated docs: {DOC_PATH}")
        failed = True
    if projection_changed:
        print("Stale projected OpenClaw config.")
        failed = True

    if failed:
        return 1

    print("Verify passed: contracts, protocols, docs, and projections are consistent.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Registry contract tool")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Validate registry contracts")
    p_validate.set_defaults(func=_run_validate_cmd)

    p_docs = sub.add_parser("generate-docs", help="Generate registry schema docs")
    p_docs.add_argument("--check", action="store_true", help="Fail if docs would change")
    p_docs.set_defaults(func=_run_generate_docs_cmd)

    p_project = sub.add_parser("project-openclaw", help="Project OpenClaw config")
    p_project.add_argument("--profile", type=str, help="Single profile name")
    p_project.add_argument("--all", action="store_true", help="Project all profiles")
    p_project.add_argument("--check", action="store_true", help="Fail if projection would change")
    p_project.set_defaults(func=_run_project_cmd)

    p_protocol = sub.add_parser(
        "check-protocol-consistency",
        help="Validate protocol consistency across docs and process manifests",
    )
    p_protocol.set_defaults(func=_run_protocol_consistency_cmd)

    p_verify = sub.add_parser("verify", help="Run full consistency checks")
    p_verify.set_defaults(func=_run_verify_cmd)

    p_verify_m2 = sub.add_parser("verify-m2", help="Run M2 runtime hardening gate checks")
    p_verify_m2.add_argument(
        "--round-dir",
        required=True,
        help="Round evidence directory (repo-relative or absolute)",
    )
    p_verify_m2.add_argument(
        "--git-range",
        help="Optional git range used for Entire-Checkpoint trailer validation",
    )
    p_verify_m2.set_defaults(func=_run_verify_m2_cmd)

    p_verify_m6 = sub.add_parser("verify-m6", help="Run M6 round evidence and gate checks")
    p_verify_m6.add_argument(
        "--round-dir",
        required=True,
        help="Round evidence directory (repo-relative or absolute)",
    )
    p_verify_m6.add_argument(
        "--git-range",
        help="Optional git range used for Entire-Checkpoint trailer validation",
    )
    p_verify_m6.set_defaults(func=_run_verify_m6_cmd)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ContractError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
