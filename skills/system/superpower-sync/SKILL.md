---
name: "superpower-sync"
description: "Synchronize Superpower change context with ANC design decisions and emit a strict sync record"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# superpower-sync

## Objective

以 Fail-Closed 方式完成 Superpower 与 ANC 设计文档的双向同步检查，输出可审计 `superpower_sync_ref` 记录。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m6-construction-plane-governance
input_contract:
  format: json
  required:
    - round_id
    - round_goal
    - superpower_ref
    - anc_design_refs
    - decision_snapshot_ref
    - sync_actor
    - trigger_mode
    - risk_level
    - checkpoint_count
    - commit_count
    - round_evidence_log_ref
    - output_ref
  validation:
    - round_id must match ^R-\d{8}-M6-[a-z0-9-]+-\d{2}$
    - superpower_ref must resolve to a Superpower change or spec item
    - anc_design_refs must be non-empty repo-relative paths
    - decision_snapshot_ref must be reachable
    - trigger_mode must be change_triggered or analyst_inspection
    - risk_level must be low or medium or high or critical
    - checkpoint_count must equal commit_count
output_contract:
  format: json
  required:
    - superpower_sync_ref
    - sync_status
    - validate_report_ref
    - status_report_ref
  machine_judgement:
    - superpower_sync_ref is generated and reachable
    - sync_status is in_sync or needs_sync or conflict or blocked
    - validate_report_ref and status_report_ref are reachable
fail_closed_rules:
  - superpower command unavailable
  - superpower project not initialized
  - superpower validation failed in strict mode
  - required sync fields missing in output record
  - checkpoint_count not equal commit_count
test_mount:
  test_doc: skills/system/superpower-sync/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  protocol_ref: docs/design/interfaces/superpower-collaboration-protocol.md
  schema_ref: docs/design/data-models/superpower-collaboration-schema.json
  wrapper_script: skills/system/superpower-sync/scripts/superpower_sync.sh
```

## Runtime Rules

1. 统一使用 `superpower` CLI 拉取 `show/status/validate` 结果。
2. 生成记录必须满足 `superpower-collaboration-schema.json`。
3. 任一检查失败时输出 `blocked` 并返回非零。
