---
name: "process-creator"
description: "Create process assets with continuity and phase-closure constraints"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# process-creator

## Objective

创建或重构流程资产（`SKILL.md/PROCESS.md/process.json`），确保符合流程标准、连续性约束与 phase 闭合约束。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-process-asset-authoring
input_contract:
  format: json
  required:
    - process_id
    - process_level
    - phases
    - control_flow
    - fail_policy
  validation:
    - process_id must be kebab-case
    - phases must be non-empty and phase-closed
    - control_flow must have bounded termination
output_contract:
  format: file_layout_and_json
  required:
    - process_manifest_path
    - process_skill_path
    - process_guide_path
  machine_judgement:
    - process.json contains mandatory standard fields
    - every phase has target_type/target_id/requires_spec
    - spec_ref is present when requires_spec=true
fail_closed_rules:
  - non-continuous lifecycle segments are hard-patched into one chain
  - phase has no AP/subprocess mapping
  - fail_policy or evidence_policy is missing
test_mount:
  test_doc: skills/meta/process-creator/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## Input Contract

- Format: json
- Required fields: process_id, process_level, phases, control_flow, fail_policy

## Output Contract

- Format: file layout + json
- Required fields: process_manifest_path, process_skill_path, process_guide_path
