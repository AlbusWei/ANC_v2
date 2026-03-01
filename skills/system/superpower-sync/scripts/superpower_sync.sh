#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: superpower_sync.sh \
  --round-id <R-YYYYMMDD-M6-...> \
  --round-goal <goal-text> \
  --superpower-ref <change_or_spec> \
  --decision-snapshot-ref <repo-relative-path> \
  --sync-actor <agent_id> \
  --trigger-mode <change_triggered|analyst_inspection> \
  --risk-level <low|medium|high|critical> \
  --checkpoint-count <int> \
  --commit-count <int> \
  --round-evidence-log-ref <repo-relative-jsonl> \
  --output-ref <repo-relative-output-json> \
  [--anc-design-ref <repo-relative-path>]...
USAGE
}

round_id=""
round_goal=""
superpower_ref=""
decision_snapshot_ref=""
sync_actor=""
trigger_mode=""
risk_level=""
checkpoint_count=""
commit_count=""
round_evidence_log_ref=""
output_ref=""
anc_design_refs=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --round-id) round_id="$2"; shift 2 ;;
    --round-goal) round_goal="$2"; shift 2 ;;
    --superpower-ref) superpower_ref="$2"; shift 2 ;;
    --decision-snapshot-ref) decision_snapshot_ref="$2"; shift 2 ;;
    --sync-actor) sync_actor="$2"; shift 2 ;;
    --trigger-mode) trigger_mode="$2"; shift 2 ;;
    --risk-level) risk_level="$2"; shift 2 ;;
    --checkpoint-count) checkpoint_count="$2"; shift 2 ;;
    --commit-count) commit_count="$2"; shift 2 ;;
    --round-evidence-log-ref) round_evidence_log_ref="$2"; shift 2 ;;
    --output-ref) output_ref="$2"; shift 2 ;;
    --anc-design-ref) anc_design_refs+=("$2"); shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$round_id" || -z "$round_goal" || -z "$superpower_ref" || -z "$decision_snapshot_ref" || -z "$sync_actor" || -z "$trigger_mode" || -z "$risk_level" || -z "$checkpoint_count" || -z "$commit_count" || -z "$round_evidence_log_ref" || -z "$output_ref" ]]; then
  echo "Missing required args" >&2
  usage
  exit 2
fi

if [[ ${#anc_design_refs[@]} -eq 0 ]]; then
  echo "At least one --anc-design-ref is required" >&2
  exit 2
fi

if [[ ! "$round_id" =~ ^R-[0-9]{8}-M6-[a-z0-9-]+-[0-9]{2}$ ]]; then
  echo "invalid round_id: $round_id" >&2
  exit 11
fi

if ! [[ "$checkpoint_count" =~ ^[0-9]+$ ]] || ! [[ "$commit_count" =~ ^[0-9]+$ ]]; then
  echo "checkpoint_count/commit_count must be integer" >&2
  exit 12
fi

if [[ "$trigger_mode" != "change_triggered" && "$trigger_mode" != "analyst_inspection" ]]; then
  echo "invalid trigger_mode: $trigger_mode" >&2
  exit 13
fi

case "$risk_level" in
  low|medium|high|critical) ;;
  *) echo "invalid risk_level: $risk_level" >&2; exit 14 ;;
esac

if [[ "$checkpoint_count" != "$commit_count" ]]; then
  echo "checkpoint_count must equal commit_count" >&2
  exit 15
fi

if ! command -v superpower >/dev/null 2>&1; then
  echo "superpower CLI not found" >&2
  exit 20
fi

workdir="$(pwd)"
out_abs="$workdir/$output_ref"
out_dir="$(dirname "$out_abs")"
mkdir -p "$out_dir"

if [[ ! -f "$workdir/$decision_snapshot_ref" ]]; then
  echo "decision_snapshot_ref not found: $decision_snapshot_ref" >&2
  exit 21
fi

if [[ ! -f "$workdir/$round_evidence_log_ref" ]]; then
  echo "round_evidence_log_ref not found: $round_evidence_log_ref" >&2
  exit 22
fi

for ref in "${anc_design_refs[@]}"; do
  if [[ ! -f "$workdir/$ref" ]]; then
    echo "anc_design_ref not found: $ref" >&2
    exit 23
  fi
done

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

show_json="$tmp_dir/show.json"
status_json="$tmp_dir/status.json"
validate_json="$tmp_dir/validate.json"
show_err="$tmp_dir/show.err"
status_err="$tmp_dir/status.err"
validate_err="$tmp_dir/validate.err"

set +e
superpower show "$superpower_ref" --type change --json --no-interactive >"$show_json" 2>"$show_err"
show_rc=$?
if [[ $show_rc -ne 0 ]]; then
  superpower show "$superpower_ref" --json --no-interactive >"$show_json" 2>"$show_err"
  show_rc=$?
fi

superpower status --change "$superpower_ref" --json >"$status_json" 2>"$status_err"
status_rc=$?
superpower validate "$superpower_ref" --type change --strict --json --no-interactive >"$validate_json" 2>"$validate_err"
validate_rc=$?
set -e

sync_status="in_sync"
if [[ $show_rc -ne 0 || $status_rc -ne 0 ]]; then
  sync_status="blocked"
elif [[ $validate_rc -ne 0 ]]; then
  sync_status="conflict"
fi

if grep -Eq 'conflict_state:[[:space:]]*unresolved|resolution:[[:space:]]*unresolved' "$workdir/$decision_snapshot_ref"; then
  sync_status="conflict"
fi

python3 - <<'PY' \
  "$out_abs" \
  "$round_id" \
  "$round_goal" \
  "$superpower_ref" \
  "$decision_snapshot_ref" \
  "$sync_actor" \
  "$trigger_mode" \
  "$risk_level" \
  "$checkpoint_count" \
  "$commit_count" \
  "$round_evidence_log_ref" \
  "$sync_status" \
  "$show_json" \
  "$status_json" \
  "$validate_json" \
  "$workdir/docs/design/data-models/superpower-collaboration-schema.json" \
  "${anc_design_refs[*]}"
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

(
    out_abs,
    round_id,
    round_goal,
    superpower_ref,
    decision_snapshot_ref,
    sync_actor,
    trigger_mode,
    risk_level,
    checkpoint_count,
    commit_count,
    round_evidence_log_ref,
    sync_status,
    show_json,
    status_json,
    validate_json,
    schema_path,
    anc_refs_raw,
) = sys.argv[1:]

anc_design_refs = [x for x in anc_refs_raw.split() if x]


def load_json(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def type_ok(value: Any, type_name: str) -> bool:
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


def unique_items(seq: List[Any]) -> bool:
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
            ok = any(type_ok(value, t) for t in expected_type)
        else:
            ok = type_ok(value, expected_type)
        if not ok:
            errors.append(f"{path}: expected type {expected_type}, got {type(value).__name__}")
            return

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} not in enum {schema['enum']!r}")

    if isinstance(value, str) and "pattern" in schema:
        if re.match(schema["pattern"], value) is None:
            errors.append(f"{path}: value {value!r} does not match pattern {schema['pattern']!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: value {value} < minimum {schema['minimum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: item count {len(value)} < minItems {schema['minItems']}")
        if schema.get("uniqueItems") and not unique_items(value):
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


record_id = "sps-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
payload = {
    "record_id": record_id,
    "round_id": round_id,
    "round_goal": round_goal,
    "module_scope": ["M6"],
    "owner": "architect",
    "superpower_ref": superpower_ref,
    "anc_design_refs": anc_design_refs,
    "decision_snapshot_ref": decision_snapshot_ref,
    "sync_status": sync_status,
    "sync_timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "sync_actor": sync_actor,
    "trigger_mode": trigger_mode,
    "inspection_profile": {
        "cadence_mode": "adaptive",
        "cadence_hint": "risk-driven",
        "primary_signal": "change_density",
    },
    "risk_level": risk_level,
    "conflict_state": {
        "has_conflict": sync_status == "conflict",
        "resolved": sync_status != "conflict",
        "resolution_ref": "" if sync_status == "conflict" else decision_snapshot_ref,
    },
    "checkpoint_count": int(checkpoint_count),
    "commit_count": int(commit_count),
    "evidence_bundle": {
        "superpower_linkage_ref": show_json,
        "anc_delta_index_ref": "",
        "sync_check_report_ref": validate_json,
        "status_report_ref": status_json,
        "round_evidence_log_ref": round_evidence_log_ref,
    },
    "sync_actions": [
        {
            "action": "superpower_show",
            "result": "ok" if load_json(show_json) is not None else "failed",
        },
        {
            "action": "superpower_status",
            "result": "ok" if load_json(status_json) is not None else "failed",
        },
        {
            "action": "superpower_validate_strict",
            "result": "ok" if load_json(validate_json) is not None else "failed",
        },
    ],
}

schema_payload = load_json(schema_path)
if not isinstance(schema_payload, dict):
    raise SystemExit(f"schema missing or invalid: {schema_path}")

errors: List[str] = []
validate_by_schema(payload, schema_payload, "payload", errors)
if errors:
    raise SystemExit("schema validation failed:\n" + "\n".join(errors))

Path(out_abs).parent.mkdir(parents=True, exist_ok=True)
with open(out_abs, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)
    f.write("\n")
PY

if [[ "$sync_status" == "blocked" || "$sync_status" == "conflict" ]]; then
  echo "Superpower sync failed with status=$sync_status" >&2
  exit 30
fi

echo "$output_ref"
