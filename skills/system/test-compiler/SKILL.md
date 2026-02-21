---
name: "test-compiler"
description: "Compile TEST.md into executable datapoints and profile bindings"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# test-compiler

## Objective

将 `TEST.md` 转换为可执行 datapoints，并产出 `tc_id -> profile_id` 绑定结果与编译证据。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: json
  required:
    - test_doc_ref
    - objective_ref
    - spec_ref
    - profile_set
  validation:
    - test_doc_ref must point to a reachable TEST.md
    - objective_ref and spec_ref must be resolvable
    - profile_set must include baseline profile
output_contract:
  format: json
  required:
    - test_datapoints_ref
    - tc_profile_map_ref
    - compile_report_ref
  machine_judgement:
    - output is valid json
    - tc_profile_map_ref contains one-to-one tc_id to profile_id mapping
    - compile_report_ref records compile summary and failures
fail_closed_rules:
  - TEST.md parse failure must return test_invalid
  - missing P0 test datapoints must fail
  - missing tc_id to profile_id mapping must fail
test_mount:
  test_doc: skills/system/test-compiler/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```
