---
name: "system-config-updater"
description: "Apply OpenClaw config patch with hash-safe guardrails"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# system-config-updater

## Objective

在审批通过后执行配置补丁并记录前后哈希与回滚状态。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-governed-openclaw-config-change
input_contract:
  format: json
  required:
    - base_hash
    - patch_raw
    - rollback_plan
  validation:
    - base_hash must be present
    - patch_raw must be valid json patch string
    - rollback_plan must be provided
output_contract:
  format: json
  required:
    - hash_before
    - hash_after
    - execution_status
    - receipt_ref
  machine_judgement:
    - hash_before and hash_after are present
    - execution_status is success or failed
    - receipt_ref is present
fail_closed_rules:
  - base hash mismatch
  - patch apply failure
  - rollback execution failure
test_mount:
  test_doc: skills/system/system-config-updater/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```
