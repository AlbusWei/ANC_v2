---
name: "openspec-sync"
description: "Synchronize OpenSpec change context with ANC design decisions and emit a strict sync record"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# openspec-sync

## Objective

以 Fail-Closed 方式完成 OpenSpec 与 ANC 设计文档的双向同步检查，输出可审计 `openspec_sync_ref` 记录。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m6-construction-plane-governance
input_contract:
  format: json
  required:
    - openspec_ref
    - anc_design_refs
    - decision_snapshot_ref
    - sync_actor
    - trigger_mode
    - risk_level
    - output_ref
  validation:
    - openspec_ref must resolve to an OpenSpec change or spec item
    - anc_design_refs must be non-empty repo-relative paths
    - decision_snapshot_ref must be reachable
    - trigger_mode must be change_triggered or analyst_inspection
    - risk_level must be low or medium or high or critical
output_contract:
  format: json
  required:
    - openspec_sync_ref
    - sync_status
    - validate_report_ref
    - status_report_ref
  machine_judgement:
    - openspec_sync_ref is generated and reachable
    - sync_status is in_sync or needs_sync or conflict or blocked
    - validate_report_ref and status_report_ref are reachable
fail_closed_rules:
  - openspec command unavailable
  - openspec project not initialized
  - openspec validation failed in strict mode
  - required sync fields missing in output record
test_mount:
  test_doc: skills/system/openspec-sync/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  protocol_ref: docs/design/interfaces/openspec-collaboration-protocol.md
  schema_ref: docs/design/data-models/openspec-collaboration-schema.json
  wrapper_script: skills/system/openspec-sync/scripts/openspec_sync.sh
```

## Runtime Rules

1. 统一使用 `openspec` CLI 拉取 `show/status/validate` 结果。
2. 生成记录必须满足 `openspec-collaboration-schema.json`。
3. 任一检查失败时输出 `blocked` 并返回非零。
