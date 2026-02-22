---
name: "config-change-gatekeeper"
description: "Validate config change prerequisites and classify risk"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.2.0"
---

# config-change-gatekeeper

## Objective

在配置变更执行前完成证据完整性校验与风险分级，违规即拒绝流转。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-governed-openclaw-config-change
input_contract:
  format: json
  required:
    - objective_ref
    - change_request
    - rollback_plan
    - evidence_refs
  validation:
    - change_request must include target_scope
    - rollback_plan must be executable
    - evidence_refs must be non-empty
output_contract:
  format: json
  required:
    - approval
    - risk_level
    - gate_report_ref
  machine_judgement:
    - approval is allow or deny
    - risk_level is low or medium or high
    - gate_report_ref is present
fail_closed_rules:
  - missing required evidence
  - missing rollback plan
  - unknown target scope
test_mount:
  test_doc: skills/system/config-change-gatekeeper/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## Runtime Tooling

1. 可执行入口：`skills/system/config-change-gatekeeper/scripts/config_change_gatekeeper_runner.py`
2. 推荐命令：
   - `python3 skills/system/config-change-gatekeeper/scripts/config_change_gatekeeper_runner.py --input <input.json> --output <output.json>`
3. W2 联动用例：`tests/m2-bpm-runtime/TC-GCC.md`（重点覆盖缺证据拒绝）
