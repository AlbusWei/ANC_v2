#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: openspec_sync.sh \
  --openspec-ref <change_or_spec> \
  --decision-snapshot-ref <repo-relative-path> \
  --sync-actor <agent_id> \
  --trigger-mode <change_triggered|analyst_inspection> \
  --risk-level <low|medium|high|critical> \
  --output-ref <repo-relative-output-json> \
  [--anc-design-ref <repo-relative-path>]...
USAGE
}

openspec_ref=""
decision_snapshot_ref=""
sync_actor=""
trigger_mode=""
risk_level=""
output_ref=""
anc_design_refs=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --openspec-ref) openspec_ref="$2"; shift 2 ;;
    --decision-snapshot-ref) decision_snapshot_ref="$2"; shift 2 ;;
    --sync-actor) sync_actor="$2"; shift 2 ;;
    --trigger-mode) trigger_mode="$2"; shift 2 ;;
    --risk-level) risk_level="$2"; shift 2 ;;
    --output-ref) output_ref="$2"; shift 2 ;;
    --anc-design-ref) anc_design_refs+=("$2"); shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$openspec_ref" || -z "$decision_snapshot_ref" || -z "$sync_actor" || -z "$trigger_mode" || -z "$risk_level" || -z "$output_ref" ]]; then
  echo "Missing required args" >&2
  usage
  exit 2
fi

if [[ ${#anc_design_refs[@]} -eq 0 ]]; then
  echo "At least one --anc-design-ref is required" >&2
  exit 2
fi

if ! command -v openspec >/dev/null 2>&1; then
  echo "openspec CLI not found" >&2
  exit 10
fi

if [[ "$trigger_mode" != "change_triggered" && "$trigger_mode" != "analyst_inspection" ]]; then
  echo "invalid trigger_mode: $trigger_mode" >&2
  exit 11
fi

case "$risk_level" in
  low|medium|high|critical) ;;
  *) echo "invalid risk_level: $risk_level" >&2; exit 12 ;;
esac

workdir="$(pwd)"
out_abs="$workdir/$output_ref"
out_dir="$(dirname "$out_abs")"
mkdir -p "$out_dir"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

show_json="$tmp_dir/show.json"
status_json="$tmp_dir/status.json"
validate_json="$tmp_dir/validate.json"

set +e
openspec show "$openspec_ref" --type change --json --no-interactive >"$show_json" 2>"$tmp_dir/show.err"
show_rc=$?
if [[ $show_rc -ne 0 ]]; then
  openspec show "$openspec_ref" --json --no-interactive >"$show_json" 2>"$tmp_dir/show.err"
  show_rc=$?
fi

openspec status --change "$openspec_ref" --json >"$status_json" 2>"$tmp_dir/status.err"
status_rc=$?
openspec validate "$openspec_ref" --type change --strict --json --no-interactive >"$validate_json" 2>"$tmp_dir/validate.err"
validate_rc=$?
set -e

sync_status="in_sync"
if [[ $show_rc -ne 0 || $status_rc -ne 0 ]]; then
  sync_status="blocked"
elif [[ $validate_rc -ne 0 ]]; then
  sync_status="conflict"
fi

python3 - <<'PY' "$out_abs" "$openspec_ref" "$decision_snapshot_ref" "$sync_actor" "$trigger_mode" "$risk_level" "$sync_status" "$show_json" "$status_json" "$validate_json" "${anc_design_refs[*]}"
import json, sys, datetime
out_abs, openspec_ref, decision_snapshot_ref, sync_actor, trigger_mode, risk_level, sync_status, show_json, status_json, validate_json, anc_refs_raw = sys.argv[1:]
anc_design_refs = [x for x in anc_refs_raw.split() if x]

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

payload = {
    "record_id": "osc-" + datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S"),
    "round_goal": "openspec-sync",
    "module_scope": ["M6"],
    "owner": "architect",
    "openspec_ref": openspec_ref,
    "anc_design_refs": anc_design_refs,
    "decision_snapshot_ref": decision_snapshot_ref,
    "sync_status": sync_status,
    "sync_timestamp": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    "sync_actor": sync_actor,
    "trigger_mode": trigger_mode,
    "inspection_profile": {
        "cadence_mode": "adaptive",
        "cadence_hint": "risk-driven",
        "primary_signal": "change_density"
    },
    "risk_level": risk_level,
    "conflict_state": {
        "has_conflict": sync_status == "conflict",
        "resolved": False,
        "resolution_ref": ""
    },
    "evidence_bundle": {
        "openspec_linkage_ref": show_json,
        "anc_delta_index_ref": "",
        "sync_check_report_ref": validate_json,
        "status_report_ref": status_json
    },
    "sync_actions": [
        {
            "action": "openspec_show",
            "result": "ok" if load_json(show_json) is not None else "failed"
        },
        {
            "action": "openspec_status",
            "result": "ok" if load_json(status_json) is not None else "failed"
        },
        {
            "action": "openspec_validate_strict",
            "result": "ok" if load_json(validate_json) is not None else "failed"
        }
    ]
}

with open(out_abs, 'w', encoding='utf-8') as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)
    f.write("\n")
PY

if [[ "$sync_status" == "blocked" || "$sync_status" == "conflict" ]]; then
  echo "OpenSpec sync failed with status=$sync_status" >&2
  exit 20
fi

echo "$output_ref"
