---
name: "template-validator"
description: "Validate templates and contract bundles before lifecycle and registry handoff"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# template-validator

## Objective

在流程推进到 lifecycle/registry 前执行模板与契约一致性检查，阻断缺字段或结构漂移资产。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-template-contract-validation
input_contract:
  format: json
  required:
    - template_ref
    - schema_ref
    - target_asset_ref
    - validation_profile
  validation:
    - template_ref must exist and be readable
    - schema_ref must point to canonical design schema
    - validation_profile must be explicit
output_contract:
  format: json
  required:
    - validation_report_ref
    - gate_decision
    - blocking_issues
  machine_judgement:
    - gate_decision is pass or fail
    - blocking_issues is explicit when fail
    - report links to schema checks and evidence
fail_closed_rules:
  - template or schema reference is missing
  - required fields mismatch cannot be auto-repaired
  - unresolved high-risk blocking issue
test_mount:
  test_doc: skills/meta/template-validator/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## Input Contract

- Format: json
- Required fields: template_ref, schema_ref, target_asset_ref, validation_profile

## Output Contract

- Format: json
- Required fields: validation_report_ref, gate_decision, blocking_issues
