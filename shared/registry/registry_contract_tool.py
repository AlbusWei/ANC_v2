#!/usr/bin/env python3
"""Registry contract validator and projection tool.

Commands:
  - validate: strict contract validation for registry files.
  - generate-docs: render human-readable schema docs from entry_contract.
  - project-openclaw: project registry data to managed OpenClaw config paths.
  - verify: run validate + capability check + docs check + projection check.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
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
REPO_PATH_RE = re.compile(r"^/Users/albus/MyProjects/ANC_v2/.+")


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


def path_exists(path_str: str) -> bool:
    return Path(path_str).exists()


def _skill_relative_key(path: Path) -> str:
    normalized = path.as_posix()
    marker = "/skills/"
    if marker not in normalized:
        return normalized
    return normalized.split(marker, 1)[1]


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
    if re.match(REPO_PATH_RE, value) is None:
        errors.append(f"{path}: path {value!r} must be under /Users/albus/MyProjects/ANC_v2/")
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
        "> 本文档由 `/Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py` 自动生成。"
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
    lines.append("python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py validate")
    lines.append(
        "python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py generate-docs --check"
    )
    lines.append(
        "python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py project-openclaw --all --check"
    )
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


def _run_verify_cmd(_args: argparse.Namespace) -> int:
    agents_payload, skills_payload, processes_payload = validate_all_registries()

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

    print("Verify passed: contracts, docs, and projections are consistent.")
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

    p_verify = sub.add_parser("verify", help="Run full consistency checks")
    p_verify.set_defaults(func=_run_verify_cmd)

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
